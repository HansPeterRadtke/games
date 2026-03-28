# Package Dependency Map

## First-release packages
### `com.hpr.eventbus`
- local package dependencies: none
- forbidden reference status: must stay free of `GameManager`, `SceneBootstrap`, `com.hpr.fpsdemo`, and local-only paths

### `com.hpr.composition`
- local package dependencies: none
- forbidden reference status: must stay free of `GameManager`, `SceneBootstrap`, `com.hpr.fpsdemo`, and local-only paths

### `com.hpr.save`
- local package dependencies: none

### `com.hpr.stats`
- local package dependencies: `com.hpr.eventbus`

### `com.hpr.inventory`
- local package dependencies: none

### `com.hpr.interaction`
- local package dependencies: `com.hpr.eventbus`, `com.hpr.inventory`

### `com.hpr.abilities`
- local package dependencies: `com.hpr.eventbus`, `com.hpr.stats`

### `com.hpr.weapons`
- local package dependencies: none

### `com.hpr.ai`
- local package dependencies: none

### `com.hpr.world`
- local package dependencies: none

## Internal packages not in the first release
- `com.hpr.foundation`
- `com.hpr.core`
- `com.hpr.input`
- `com.hpr.ui`
- `com.hpr.bootstrap`
- `com.hpr.fpsdemo`

## Validation combinations
- `com.hpr.composition` + `com.hpr.eventbus`
- `com.hpr.eventbus` + `com.hpr.stats`
- `com.hpr.inventory` + `com.hpr.interaction`
- `com.hpr.eventbus` + `com.hpr.stats` + `com.hpr.abilities`
- `com.hpr.weapons` + `com.hpr.ai` + `com.hpr.world`
- full first-release set together
