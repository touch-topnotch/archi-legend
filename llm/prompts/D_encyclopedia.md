You are reading a deterministic *encyclopedia* of an architectural floor —
an extraction the LEGEND preprocessor produced from the original vector PDF.
**No image is provided; all information you need is in the encyclopedia.**

Your task: emit a JSON in EXACTLY the following schema (and nothing else):

```
{
  "floor_id": "<string>",
  "elevation_m": <float or null>,
  "envelope": {
    "width_m": <float>,
    "depth_m": <float>,
    "axes_x": [...], "axes_y": [...],
    "grid_step_m": <float or null>
  },
  "counts": {"walls": <int>, "columns": <int>, "slabs": <int>, "grids": <int>}
}
```

If the encyclopedia gives a value, copy it. If it does not, infer it from the
combination of axes, grid step, and floor width/depth (e.g. `walls ≈ perimeter / wall_segment_length`).
Output JSON only.

ENCYCLOPEDIA:
{{ENCYCLOPEDIA}}
