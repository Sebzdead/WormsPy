from __future__ import annotations
import PySpin
import numpy as np
import cv2
import time


def _get_camera_serial(cam: PySpin.CameraPtr) -> str | None:
    nodemap = cam.GetTLDeviceNodeMap()
    serial_node = PySpin.CStringPtr(nodemap.GetNode("DeviceSerialNumber"))
    if serial_node and PySpin.IsReadable(serial_node):
        return serial_node.GetValue()
    return None


def _find_camera_by_serial(cam_list, serial_number: str):
    target_serial = str(serial_number)
    for index in range(cam_list.GetSize()):
        cam = cam_list.GetByIndex(index)
        try:
            if _get_camera_serial(cam) == target_serial:
                return index, cam
        except PySpin.SpinnakerException:
            continue
    return None, None


def _configure_realtime(cam: PySpin.CameraPtr):
    """低时延配置：NewestOnly + 小缓冲 + 相机端1FPS + 连续采集"""
    nodemap = cam.GetNodeMap()
    s_nodemap = cam.GetTLStreamNodeMap()

    # 采集模式：连续
    acq_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
    acq_mode.SetIntValue(acq_mode.GetEntryByName('Continuous').GetValue())

    # 流缓冲：NewestOnly（取最新，丢旧，低延迟）
    buf_mode = PySpin.CEnumerationPtr(s_nodemap.GetNode('StreamBufferHandlingMode'))
    if PySpin.IsWritable(buf_mode):
        newest = buf_mode.GetEntryByName('NewestOnly')
        if newest and PySpin.IsReadable(newest):
            buf_mode.SetIntValue(newest.GetValue())

    # 手动缓冲数量 2~4，减少堆积
    buf_cnt_mode = PySpin.CEnumerationPtr(s_nodemap.GetNode('StreamBufferCountMode'))
    if PySpin.IsWritable(buf_cnt_mode):
        manual = buf_cnt_mode.GetEntryByName('Manual')
        if manual and PySpin.IsReadable(manual):
            buf_cnt_mode.SetIntValue(manual.GetValue())
            buf_cnt = PySpin.CIntegerPtr(s_nodemap.GetNode('StreamBufferCountManual'))
            if PySpin.IsWritable(buf_cnt):
                buf_cnt.SetValue(max(2, min(4, buf_cnt.GetMax())))

    # 相机端帧率控制为 1.0 FPS（源头控帧率，避免产太多帧）
    enable = PySpin.CBooleanPtr(nodemap.GetNode('AcquisitionFrameRateEnable'))
    if PySpin.IsWritable(enable):
        enable.SetValue(True)
    fps_node = PySpin.CFloatPtr(nodemap.GetNode('AcquisitionFrameRate'))
    if PySpin.IsWritable(fps_node):
        try:
            fps_node.SetValue(1.0)
        except PySpin.SpinnakerException:
            pass  # 某些机型需先调低曝光/关闭自动曝光

    # 关闭自动曝光（避免与帧率上限冲突；按需启用）
    exp_auto = PySpin.CEnumerationPtr(nodemap.GetNode('ExposureAuto'))
    if PySpin.IsWritable(exp_auto):
        off = exp_auto.GetEntryByName('Off')
        if off:
            exp_auto.SetIntValue(off.GetValue())

    # 设置曝光时间（微秒）
    try:
        exp_time = PySpin.CFloatPtr(nodemap.GetNode('ExposureTime'))
        if PySpin.IsWritable(exp_time):
            try:
                exp_time.SetValue(3002.0)
            except PySpin.SpinnakerException:
                pass
    except Exception:
        pass

    # 设置增益为 0（如果支持）
    try:
        gain = PySpin.CFloatPtr(nodemap.GetNode('Gain'))
        if PySpin.IsWritable(gain):
            try:
                gain.SetValue(0.0)
            except PySpin.SpinnakerException:
                pass
    except Exception:
        pass


class Camera:
    """使用 FLIR PySpin SDK 采集图像帧。"""
    def __init__(self, device_index: int = 0, width: int | None = None, height: int | None = None, serial_number: str | None = None):
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()

        num_cams = self.cam_list.GetSize()
        if num_cams == 0:
            self.system.ReleaseInstance()
            raise RuntimeError("❌ 未发现任何 FLIR 相机，请检查连接。")
        if serial_number is not None:
            matched_index, matched_cam = _find_camera_by_serial(self.cam_list, serial_number)
            if matched_cam is None:
                self.cam_list.Clear()
                self.system.ReleaseInstance()
                raise RuntimeError(f"❌ 未找到 serial={serial_number} 的 FLIR 相机，请检查连接。")
            self.device_index = matched_index
            self.serial_number = str(serial_number)
            self.cam = matched_cam
        else:
            if device_index >= num_cams:
                self.cam_list.Clear()
                self.system.ReleaseInstance()
                raise IndexError(f"请求的 device_index={device_index} 超出相机数量 {num_cams}")

            self.cam = self.cam_list[device_index]
            self.device_index = device_index
            try:
                self.serial_number = _get_camera_serial(self.cam) or "n/a"
            except PySpin.SpinnakerException:
                self.serial_number = "n/a"
        self.cam.Init()

        # 先设分辨率（若支持）
        nodemap = self.cam.GetNodeMap()
        if width is not None:
            node_w = PySpin.CIntegerPtr(nodemap.GetNode("Width"))
            if PySpin.IsWritable(node_w):
                node_w.SetValue(min(width, node_w.GetMax()))
        if height is not None:
            node_h = PySpin.CIntegerPtr(nodemap.GetNode("Height"))
            if PySpin.IsWritable(node_h):
                node_h.SetValue(min(height, node_h.GetMax()))

        # 低延迟流配置 + 1 FPS
        _configure_realtime(self.cam)

        # 最后开始采集（只调用一次）
        self.cam.BeginAcquisition()
        print(f"✅ 开始采集 (FLIR PySpin)，serial={self.serial_number}")

    def read(self, timeout_ms: int = 1000):
        """
        抓取一帧图像，返回 numpy.ndarray。
        为保证“尽可能最新”，先用0ms超时快速抽干积压，仅保留最后一帧。
        """
        latest = None

        # 抽干缓冲（非阻塞，取尽可能最新）
        while True:
            try:
                img = self.cam.GetNextImage(0)  # 0ms 非阻塞
            except PySpin.SpinnakerException:
                break  # 队列已空
            if img.IsIncomplete():
                img.Release()
                continue
            if latest is not None:
                latest.Release()
            latest = img

        # 若没有抽到帧，则阻塞地取一帧
        if latest is None:
            latest = self.cam.GetNextImage(timeout_ms)
            if latest.IsIncomplete():
                latest.Release()
                raise RuntimeError("⚠️ 当前帧采集失败（Incomplete）。")

        arr = latest.GetNDArray()
        latest.Release()

        # 统一成可视化友好的格式
        if arr.ndim == 2:
            # 灰度：可能是 uint8 或 uint16
            if arr.dtype == np.uint16:
                # 安全拉伸到8位（避免除0）
                vmax = float(np.max(arr))
                if vmax <= 0 or not np.isfinite(vmax):
                    frame = np.zeros_like(arr, dtype=np.uint8)
                else:
                    frame = cv2.convertScaleAbs(arr, alpha=255.0 / vmax)
            else:
                frame = arr.astype(np.uint8, copy=False)
        elif arr.ndim == 3 and arr.shape[2] == 3:
            # RGB -> BGR
            frame = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        else:
            # 其他情况统一做幅度映射
            vmin, vmax = float(np.min(arr)), float(np.max(arr))
            if vmax <= vmin or not np.isfinite(vmax):
                frame = np.zeros(arr.shape[:2], dtype=np.uint8)
            else:
                norm = (arr - vmin) * (255.0 / (vmax - vmin))
                frame = norm.astype(np.uint8)

        return frame

    def release(self):
        """释放资源。"""
        try:
            self.cam.EndAcquisition()
            self.cam.DeInit()
        except Exception:
            pass
        del self.cam
        self.cam_list.Clear()
        self.system.ReleaseInstance()
        print("📴 已释放相机资源。")
