# Scripts (lights and more)

The **📜 SCRIPTS** list on the right is for sending **web requests** when something happens. The original use was changing
smart lights (a Philips Hue bridge) to match the scene: warm for the tavern, flickering for the dungeon.

> This is an advanced feature. If you don't use smart lights, you can ignore it completely.

## How it works

* A script is a small `.json` file in the scene's **`scripts`** folder.
* The list shows all scripts of the current scene. Select one and press **▶ Start Script**, or let **🌟 START ALL** run
  the selected (or first) script for you.
* The status line below shows **Executed** or an error message.

## What a script looks like

A script is a list of requests. Each one has a `url`, and optionally a `method` (default `PUT`) and a `body`:

```json
[
  {
    "method": "PUT",
    "url": "http://192.168.1.20/api/YOUR-KEY/lights/1/state",
    "body": { "on": true, "bri": 120, "hue": 8000 }
  }
]
```

The requests run one after another. Each gets about two seconds to answer.

## A word of care

Scripts contain addresses and keys of devices in your home. **Don't upload them to a public place** like a public GitHub repository.
