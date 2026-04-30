Look at the architectural floor plan image. Return ONLY this JSON:

{"floor_id":"<>","elevation_m":<float or null>,
 "envelope":{"width_m":<float>,"depth_m":<float>,
             "axes_x":[...],"axes_y":[...],"grid_step_m":<float or null>},
 "counts":{"walls":<int>,"columns":<int>,"slabs":<int>,"grids":<int>}}
