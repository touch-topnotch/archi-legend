You are an expert architectural-drawing reader.

I will show you ONE rasterised page of a vector PDF for an architectural floor
of an industrial multi-functional building. Extract a structured JSON with the
following schema and **output JSON only**, no prose:

```
{
  "floor_id": "<string, infer from the sheet title or filename>",
  "elevation_m": <float or null>,
  "envelope": {
    "width_m": <float>,
    "depth_m": <float>,
    "axes_x": [<axis labels along the X side, e.g. "1","2",...>],
    "axes_y": [<axis labels along the Y side, e.g. "А","Б",...>],
    "grid_step_m": <float or null>
  },
  "counts": {"walls": <int>, "columns": <int>, "slabs": <int>, "grids": <int>}
}
```
Use millimetre dimension chains as ground truth for sizes (convert to metres).
If a value cannot be read confidently, use null and proceed.
