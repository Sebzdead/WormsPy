import cv2

try:
    import PySpin
except ModuleNotFoundError:
    PySpin = None


def check_flir_cameras():
    if PySpin is None:
        print("⚠️ 未安装 PySpin，无法直接检查 SpinView/FLIR 相机。")
        return []

    print("🔍 检查 FLIR / SpinView 相机...")
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()

    available = []
    try:
        count = cam_list.GetSize()
        if count == 0:
            print("⚠️ 未检测到任何 FLIR 相机。")
            return available

        for index in range(count):
            cam = cam_list.GetByIndex(index)
            try:
                cam.Init()
                nodemap = cam.GetTLDeviceNodeMap()
                serial_node = PySpin.CStringPtr(nodemap.GetNode("DeviceSerialNumber"))
                model_node = PySpin.CStringPtr(nodemap.GetNode("DeviceModelName"))
                serial = serial_node.GetValue() if serial_node and PySpin.IsReadable(serial_node) else "n/a"
                model = model_node.GetValue() if model_node and PySpin.IsReadable(model_node) else "n/a"
                print(f"✅ FLIR 相机 {index} 可用: model={model}, serial={serial}")
                available.append(index)
            except PySpin.SpinnakerException as exc:
                print(f"❌ FLIR 相机 {index} 初始化失败: {exc}")
            finally:
                try:
                    cam.DeInit()
                except Exception:
                    pass
    finally:
        try:
            del cam
        except Exception:
            pass
        cam_list.Clear()
        system.ReleaseInstance()

    if not available:
        print("⚠️ 没有检测到可用的 FLIR 相机。")
    else:
        print(f"\n可用 FLIR 相机索引列表: {available}")

    return available


if __name__ == "__main__":
    flir_available = check_flir_cameras()
