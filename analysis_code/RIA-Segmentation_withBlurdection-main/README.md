# RIA Segmentation Pipeline

Local analysis pipeline for whole-worm segmentation, RIA crop extraction, head-angle calculation, RIA alignment, and ROI intensity extraction.

## Step Order

1. `1ConvertTIFFtoStack.py`
2. `2TIFF2JPG.py`
3. `3SegmentWorm.py`
4. `4AutoCrop.py`
5. `5WormSkeletonHeadAngle.py`
6. `6CropTIFF2JPG.py`
7. `7AlignRIA_ECC.py`
8. `8ROIIntensity.py`

`RunPipeline1to7.py` runs steps 1-7 in sequence.

```powershell
python RunPipeline1to7.py
python RunPipeline1to7.py --start 4 --end 7
```

## Local Files Not Tracked

Data, results, training sets, logs, temporary SAM2 chunks, image previews, TIFF/JPG/PNG files, and model checkpoints are intentionally ignored by git.

Expected local model locations:

- `training_runs/ria_detector/weights/best.pt`
- `training_runs/worm_detector/weights/best.pt`

These files should be copied or trained locally before running the detector-assisted steps.
