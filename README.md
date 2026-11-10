# unimag-opi
unified view of Magnets


## PV Interface for `mag_channel.bob`

The `mag_channel.bob` OPI provides a unified interface for monitoring and controlling magnet channels. It uses the following Process Variables (PVs), parameterized via macros for flexibility:

- **Current Readback PV (`CURRENT_RB`)**  
  Displays the current readback value for the magnet channel.  
  PV format: `$(P):$(R):CURRENT_RB`

- **Current Setpoint PV (`CURRENT_SP`)**  
  Allows the user to set the desired current for the magnet channel.  
  PV format: `$(P):$(R):CURRENT_SP`

- **Status PV (`STATE_RB`)**  
  Shows the current status or state of the magnet channel.  
  PV format: `$(P):$(R):STATE_RB`

- **Set Status PV (`STATE_SP`)**  
  Enables the user to change the status or mode of the channel (e.g., via ON, STBY, RESET buttons).  
  PV format: `$(P):$(R):STATE_SP`

### Possible Values for `STATE_RB` and `STATE_SP`

The status PVs represent the operational state of the magnet channel. Possible values include:

- 0 `OFF` – Magnet is powered off or inactive
- 1 `ON` – Magnet is active and powered
- 2 `STANDBY` – Magnet is in standby mode
- 3 `FAULT` – Magnet has detected a fault condition (alarm high)
- 4 `EXT_INTLK`  –triggered by external interlock (alarm high)
- 5 `CONN_FAULT` -triggered by communication errors (alarm high)
- 8.. additional, device specific states (e.g. Danfysik `RAMPING`, `POL_CHANGE`)

`STATE_RB` is the state of the device. A setpoint or state not reached is a
software state, reported in `STATE_SM` (`SPNOTSET` / `STATENOTSET`, see below).
Only the Hazemeyer CITBus cubicle, which has no `STATE_SM`, still reports a
state not reached in `STATE_RB` as `7 ST_NOT_REACHED` (MAJOR).

#### UNIMAG Configuration

| Parameter | Description | Default | Units |
|-----------|-------------|---------|-------|
| `SET_TOLERANCE` | Current setpoint tolerance | 1.0 | Amperes |
| `ZERO_TOLERANCE` | Zero current tolerance | 0.5 | Amperes |
| `SET_TIMEOUT_S` | Setpoint timeout (resets on progress) | 30 | Seconds |
| `RETRY` | Number of times a command (setpoint, state) is sent again when not applied | 3 | - |

**Important**: The timeout timer resets whenever the power supply makes progress toward the target current.

#### UNIMAG State Machine (`STATE_SM`)

Every UNIMAG power supply publishes what it is doing in
`$(P):$(R):STATE_SM`. The ones that also send a command again (OCEM E642,
Hazemeyer CITBus channels) give the retries of the current command in
`$(P):$(R):RETRY_COUNT`:

| Value | State | Meaning | Severity |
|-------|-------|---------|----------|
| 0 | `READY` | Idle, last command done | |
| 1 | `GOTOSET` | Going to the current setpoint (within `SET_TOLERANCE`) | |
| 2 | `GOTOSTATE` | Going to the commanded state | |
| 3 | `GOZERO` | Going to zero current (within `ZERO_TOLERANCE`) | |
| 4 | `GOPOS` | Changing polarity to positive | |
| 5 | `GONEG` | Changing polarity to negative | |
| 6 | `SPNOTSET` | Setpoint not reached within `SET_TIMEOUT_S` (after `RETRY` retries where supported) | MINOR |
| 7 | `STATENOTSET` | State not reached within `SET_TIMEOUT_S` (after `RETRY` retries where supported) | MAJOR |

Where supported, a command not applied within `SET_TIMEOUT_S` is sent again
up to `RETRY` times. `GOPOS` / `GONEG` only appear on supplies that switch
polarity in software (OCEM E642, Danfysik, Maccaferri, EEI); `GOZERO` while
going to a zero setpoint or ramping down before a polarity change. The
setpoint check is armed by the first `CURRENT_SP` written after the IOC
starts, so a supply left running is not reported as `SPNOTSET`. `SPNOTSET` / `STATENOTSET` stay until the next command; `STATE_SP` =
`RESET` interrupts the retries and brings `STATE_SM` back to `READY`.


These values are displayed in the status widgets and can be set using the action buttons in the OPI.

### Additional Macros

- **NAME**: The name of the magnet or channel, displayed in the interface.
- **ZONE**: The zone or area associated with the channel.
- **OPI**: The path to a custom control OPI file for advanced actions.

### Widget Overview

- **Readout**: Displays the current value.
- **SetPoint**: Allows entry of a new current setpoint.
- **Status**: Shows the current operational state.
- **Set Status**: Provides buttons to change the channel's state (ON, STBY, RESET).
- **Custom Control Button**: Opens a custom OPI for advanced control if configured.
- **Checkbox**: Used for selection logic in multi-magnet views.

### PV Naming Convention

All PVs are constructed using macro substitutions `$(P)` (prefix) and `$(R)` (record or channel identifier), ensuring the interface can be reused for multiple magnet channels by simply changing the macro values.

---

For more details on the OPI layout and macro usage, refer