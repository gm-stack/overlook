# doorlock UDP protocol #

In the example configuration, the service sends to the multicast UDP group 239.0.0.1 port 3300.

Messages are encoded as JSON.  All messages have attribute `event` which determines the event type being transmitted.

## Event Types ##

### `doorUnlock` ###

Fired when the door is unlocked successfully.  Passes the following addditional parameters:

* `user`: The username of the person who swiped their card
* `label`: A user-specific identifier for the card, for example, "metrocard".
* `id`: The card's serial number, encoded as base16.

### `disabledCard` ###

Fired when the door is not unlocked, because a known card is disabled in the database.

Passes the same parameters as `doorUnlock`.

### `unknownCard` ###

Fired when the door is not unlocked, because an unknown card was used.  Passes the following additional parameter:

* `id`: The card's serial number, encoded as base16.

### `exitButton` ###

Fired when the door's exit button is pressed.

Has no parameters.

### `fridgeAlarm` ###

Fired when the fridge door has been left open for too long.  Passes the following additional parameter:

* `time`: The number of seconds the fridge door has been left open.

### `fridgeAlarmStop` ###

Fired when the fridge door was closed after the alarm was triggered.

Has no parameters.
