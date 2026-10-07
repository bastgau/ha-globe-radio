# Globe Radio

Home Assistant custom integration that plays a radio station on a Music Assistant player with its name and logo. It is the companion of the [radio-globe-card](https://github.com/bastgau/ha-cards/tree/main/www/radio-globe-card).

Music Assistant ignores the `title` and `thumb` sent with `media_player.play_media` (checked in `homeassistant/components/music_assistant/media_player.py`: only `media_id`, `enqueue`, `announce` and `radio_mode` are read). This integration adds the station to Music Assistant first (`builtin/add_radio`), then plays it.

## Service

`globe_radio.play_station`

| Field       | Required | Description                                                                 |
| ----------- | -------- | --------------------------------------------------------------------------- |
| `entity_id` | yes      | Music Assistant media player                                                |
| `url`       | yes      | Stream URL                                                                  |
| `name`      | yes      | Station name, stored as `[Globe Radio] <name>`                              |
| `image_url` | no       | Full logo URL, reachable from the Music Assistant server (no local path)    |

`globe_radio.cleanup`

Removes the stations added by `play_station` (name starting with `[Globe Radio]`) from the Music Assistant library. Favorites and the station a queue is playing or has paused are kept.

| Field     | Required | Description                                                          |
| --------- | -------- | -------------------------------------------------------------------- |
| `dry_run` | no       | `true` only lists what would be removed. The response holds `removed` and `skipped` |

Example automation, every night at 4:00:

```yaml
automation:
  - alias: Clean up Globe Radio stations
    triggers:
      - trigger: time
        at: "04:00:00"
    actions:
      - action: globe_radio.cleanup
```

The removal uses `music/library/remove_item`, which Music Assistant documents as destructive (the item and its dependants). What happens when a station is removed while it plays is not tested: `cleanup` skips the stations of non-idle queues.

## Install

Copy `custom_components/globe_radio/` to `/config/custom_components/`, or add this repository to HACS as a custom repository. Add this to `configuration.yaml` and restart:

```yaml
globe_radio:
```

## Status

Minimal first version, **not tested yet**. To check on a real installation:

- the value returned by `builtin/add_radio` (a `uri` is expected) and that `play_media` accepts it;
- the delay of the library sync that `add_radio` triggers after one second;
- that the Music Assistant user used by the integration may write to the library;
- `cleanup`: the fields returned by `music/radios/library_items` (`favorite`, `name`, `item_id`) and by `player_queues/all` (`state`, `current_item.media_item.name`) were read in the server code only. Run it with `dry_run: true` first.

Every station played stays in the Music Assistant library under the `[Globe Radio]` prefix until `globe_radio.cleanup` runs.
