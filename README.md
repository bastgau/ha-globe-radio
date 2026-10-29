# Globe Radio

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-custom%20integration-41BDF5.svg)](https://www.home-assistant.io)

Play an internet radio station on a [Music Assistant](https://music-assistant.io) player from Home Assistant, **with its name and logo**.

## Why

Music Assistant ignores the `title` and `thumb` sent with `media_player.play_media`: only `media_id`, `enqueue`, `announce` and `radio_mode` are read. Playing a bare stream URL therefore shows the URL instead of the station name, and no artwork.

Globe Radio works around this. It first adds the station to the Music Assistant library (`builtin/add_radio`) with its name and logo, then plays it from there. Any dashboard, script or automation that knows a stream URL, a name and a logo can then play a proper radio station.

## Requirements

- Home Assistant with the [Music Assistant](https://www.home-assistant.io/integrations/music_assistant/) integration set up and loaded
- At least one Music Assistant media player

## Installation

### Installation via HACS

1. Add this repository as a custom repository to HACS:

[![Add Repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=bastgau&repository=ha-globe-radio&category=Integration)

2. Use HACS to install the integration.
3. Add the integration to your `configuration.yaml` (see [Configuration](#configuration)).
4. Restart Home Assistant.

### Manual installation

1. Download the integration files from the GitHub repository.
2. Copy `custom_components/globe_radio/` into the `custom_components/` folder of your Home Assistant configuration.
3. Add the integration to your `configuration.yaml` (see [Configuration](#configuration)).
4. Restart Home Assistant.

## Configuration

Globe Radio is set up in YAML, there is no configuration page in the UI. Add this to `configuration.yaml`, then restart Home Assistant:

```yaml
globe_radio:
```

There is no other option.

## Actions

### `globe_radio.play_station`

Adds the station to Music Assistant, then plays it on the given player.

| Field       | Required | Description                                                              |
| ----------- | -------- | ------------------------------------------------------------------------ |
| `entity_id` | yes      | Music Assistant media player                                             |
| `url`       | yes      | Stream URL                                                               |
| `name`      | yes      | Station name, stored as `[Globe Radio] <name>`                           |
| `image_url` | no       | Full logo URL, reachable from the Music Assistant server (no local path) |

```yaml
action: globe_radio.play_station
data:
  entity_id: media_player.living_room
  url: "https://stream.example.com/radio.mp3"
  name: Radio Example
  image_url: "https://example.com/logos/radio-example.png"
```

Every station played stays in the Music Assistant library under the `[Globe Radio]` prefix until `globe_radio.cleanup` runs.

### `globe_radio.cleanup`

Removes the stations added by `play_station` (name starting with `[Globe Radio]`) from the Music Assistant library. Favorites and the station a queue is playing or has paused are kept.

| Field     | Required | Description                                                                         |
| --------- | -------- | ----------------------------------------------------------------------------------- |
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

The removal uses `music/library/remove_item`, which Music Assistant documents as destructive (the item and its dependants). Run `cleanup` with `dry_run: true` first to check what would be removed.
