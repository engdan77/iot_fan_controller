# Internet-Of-Things Fan Controller

[TOC]

<img src="https://docs.zerynth.com/latest/_images/nodemcu3.jpg" style="zoom:50%;" />

## The store and reflections behind this project

I noticed that my Macbook Pro became rather warm 🥵 while working and thought I would drill a hole and place fan under the surface of the laptop in the desk, I also remembered I both had a few [ESP8266](https://en.wikipedia.org/wiki/ESP8266) ([NodeMCU v3](https://docs.zerynth.com/latest/official/board.zerynth.nodemcu3/docs/index.html), let's call it [MCU](https://en.wikipedia.org/wiki/Microcontroller)) and [DHT22](https://www.sparkfun.com/datasheets/Sensors/Temperature/DHT22.pdf) in box somewhere to be used in some context and this was a good oportunity get use of those allowing the temperature 🌡 of the surface to <u>control</u> whether that fan should be <u>on or off</u> to avoid unnecesary noise. I first begun thinking I could spend a moment soldering the this together with a [BC547](https://en.wikipedia.org/wiki/BC548) <u>transistor</u> to allow a 3.3v from [GPIO](https://en.wikipedia.org/wiki/General-purpose_input/output) of the MCU allow a higher voltage 12v to the <u>fan</u> ♒︎. Easy-peasy.. hmm, it might also be nice to have a <u>button</u> 🔘 to be able to force an on/off so let's put there as well to another GPIO... but before trying this on a breadboard, I got caught with some fundemental trap while verifying the transistor working, and thankfully to my electronic-genius to friend [Erik](https://www.linkedin.com/in/erik-wallebom-240792178) helped me get it right.. Now next soldering .. and a lot of cursing - honestly it must be difficult finding anyone worse than me soldering but finally those pieces in its place and now to the part I find most fun, programming Micropython to do the work for me.
With a few lines of code l just doing a quick while-loop to determine the temperatur and supply voltage to a GPIO was extremely easy, but it made me think bigger .. wouldn't it be nice to have a [RESTful-API](https://en.wikipedia.org/wiki/Representational_state_transfer) to allow me to control this fan through the <u>network</u> ...? Well, that in itself is easily done .. now, the challenge here is concurrency - we do need to assure we maintain the state of the button, and the temperature at the same time as we need to assure that the MCU also responds to incoming TCP/IP packets the code needs to following [asynchronous paradigm](https://en.wikipedia.org/wiki/Asynchrony_(computer_programming)) due to the fact that this is a single-core RISC-processor without support for threading. 🤔 Thankfully Micropython does support asyncio that makes this possible by async/await keywords. To save some efforts writing the web-framework I found this nice [picoweb](https://github.com/pfalcon/picoweb) to the rescue built as async. Now for readability I developed classes for button-presses and temperature with builtin subroutines checking their states, now exposing these to the web-framework there was a need to subclass a couple of methods to allow this.... now almost there ... now I was able to use REST to also check status and also suppled methods to update configuration... hmm .. wouldn't it be even nicer to build a [captive portal](https://en.wikipedia.org/wiki/Captive_portal) 📲 that many products does have to simplify configuration, I went into the rabbit-hole learning everything about captive portals that involves quite a lot of spoofing-mechanism not only involving HTTP, DHCP but also DNS-requests .. I found some projects built trying this out, but didn't find it stable enough so I left this *(for the time beeing at least)* with some better insight of this for the future. I did manage to supply code that allows the MCU to broadcast an essid "fan_control" that allows one to access if the Wifi configured is not properly connected - this is allows me to alway configure the device if Wifi isn't working.The captive portal gave me the idea that it would also be nice to have some sort of a <u>web-configuration-interface</u>  for the initial configuration instead of hard-code configuration or send as REST (JSON) .. found some boilerplate for that but now I dug deeper into the world of CSS to make it look nice, [AJAX](https://en.wikipedia.org/wiki/Ajax_(programming)) using [JQuery](https://en.wikipedia.org/wiki/JQuery) to allow me to nicely have the web-interface with help of my REST-API in real-time (or near) present the state of the fan and what the current temperature is. With this interface you could also configure Wifi-settings ... now since I am happy user of the great Home Assistant (HASS) project where its heart of home-automation is an MQTT-broker, I also thought that I might as well add [MQTT](https://en.wikipedia.org/wiki/MQTT)-client to allow this MCU to inform my HASS what the temperature currently is... That's cool, that way I can e.g. have the home inform me by shouting to me through the SONOS-speakers when my laptop burns in flames 🔥 😜 .. Ok, cool .. now while squeezing more and more Python-code while the project grew successfully it finally more and more often got something like.. 

```
MemoryError: memory allocation failed, allocating 4084 bytes
```

 Oh dear ... now what can one expect from a such small device with a cost equallent to a chocolate-cake .. I read and learned that NodeMCU v3 in particular has 4MB flash, which is the "permanent" storage which is quite a lot, but now it turns out that <u>this MCU has roughly 50KB of usable RAM to use</u> (in fact see like 21KB after [REPL](https://docs.micropython.org/en/latest/esp8266/tutorial/repl.html) been started)  .. Slightly less than Commode 64 😂 so quite impressive that you can really do this much with that little memory and considering what you get for the same cost as you would pay for a candybar 🍫. I've learnt that one could save memory by [freezing](http://docs.micropython.org/en/v1.9.3/unix/reference/constrained.html) ❄️ your modules into [byte-code](https://opensource.com/article/18/4/introduction-python-bytecode) *(as you may know Micropython does a compilation before you run the code)*, and you do this by adding those **.py** file into the "modules" folder before compiling a binary you can upload to the MCU, there was also another lesson learned that to allow Micropython to address all of those 4MB flash you would need to configre it to do so instead of those defaul 512KB flash that the even slimmer/cheaper models ESP-01 does have.. this was described in this [thread](https://github.com/micropython/micropython/issues/2700#issuecomment-287737238). Now also thanks to docker-images such as [this](https://hub.docker.com/r/fcollova/micropython-docker-build/) one made it easy to build your own image without the hassle of configuring the cross-compiler. Now since it is better being safe than sorry, even though since I've build a frozen code saving RAM and yet no memory allocation failures it turns out that one could easily implement a [Watch Dog Timer](https://en.wikipedia.org/wiki/Watchdog_timer) 🐕 that make sure that assure that in case of a larger exception we have an interrupt that assures the MCU resets itself... and now if MQTT is being enabled one would easily get informed when this happens.

Now .. finally, with a binary-image of less than **610KB** uploaded to the MCU it now supports

- [x] Fan control by
  - [x] Temperatures based on under/above threshold
  - [x] Button clicks
  - [x] REST-API
  - [x] Web-interface
- [x] Temperatue readings by
  - [x] Web-interface
  - [x] Push to MQTT-queue (for future home automation)
- [x] Configuration by
  - [x] Web-interface
  - [x] REST-API
- [x] Watch Dog in case of unpredictable errors

All coded using async ... and now with the cost around a couple of € .. personally thinking that is rather awesome 😁👍🏻

## Requirements

- Hardware 
  - [ESP8266](https://www.aliexpress.com/item/32965931916.html?spm=a2g0o.productlist.0.0.50497549rQyoZ3&algo_pvid=19b23545-dd7d-4224-96ae-2025f037db1d&algo_expid=19b23545-dd7d-4224-96ae-2025f037db1d-11&btsid=2716d10b-fd90-4166-a546-d6686758d8b3&ws_ab_test=searchweb0_0,searchweb201602_7,searchweb201603_53) (NodeMCUv3 recommend), now this should run on any MCU with support for GPIO such as big-brother ESP32
  - [DHT22](https://www.aliexpress.com/item/32910648572.html?spm=a2g0o.productlist.0.0.5383bd0cTkfcaW&algo_pvid=a34e1391-202f-4ff3-8974-a31f5f3451f9&algo_expid=a34e1391-202f-4ff3-8974-a31f5f3451f9-3&btsid=d639b7e2-cf88-4542-9e29-db53ef2936f9&ws_ab_test=searchweb0_0,searchweb201602_7,searchweb201603_53)
  - [Switch](https://www.aliexpress.com/item/4000463252893.html?spm=a2g0o.productlist.0.0.4af577fe3nffFn&algo_pvid=25389959-e10b-4426-9b76-fcf7e7bcd5f3&algo_expid=25389959-e10b-4426-9b76-fcf7e7bcd5f3-0&btsid=74b1be02-14c9-4d4e-9df8-e00a0a364eb0&ws_ab_test=searchweb0_0,searchweb201602_7,searchweb201603_53)
  - A computer [fan](https://www.aliexpress.com/item/32847821588.html?spm=a2g0o.productlist.0.0.52245fa8RqIXVz&algo_pvid=c96e71f9-177e-449e-9124-adf1ce8614b6&algo_expid=c96e71f9-177e-449e-9124-adf1ce8614b6-3&btsid=bc1f37e1-9dda-4a18-85a5-e184a3264121&ws_ab_test=searchweb0_0,searchweb201602_7,searchweb201603_53)
  - Soldering iron, solder and some wires
  - Willingness to build following the sketch below 😉
- A computer to upload the data from

## Hardware design

This is a sketch that show how you would solder if you're using an NodeMCU.

[![https://i.ibb.co/rkmCtnR/fan-control-board-schem.png](https://i.ibb.co/rkmCtnR/fan-control-board-schem.png)](https://ibb.co/tB47hyT)



## Install using pre-built image

You can basically download tool such as esptool to upload it using

```bash
esptool.py --port /dev/cu.usbserial-1410  --baud 115200 write_flash --flash_size=detect 0 ./firmware-fan-control.bin
```

And replace the serial port you are using

## How does it work?

First time you boot it....





## Build a frozen image from source and upload to ESP8266

### Manually build binary image without upload

Build the docker image of the master branch. The custom Dockerfile will add src as frozen and update the entrypoint

```bash
  docker build -t fancontrol-build . && docker create --name fancontrol-build fancontrol-build-container && docker cp fancontrol-build-container:/micropython/ports/esp8266/build-GENERIC/firmware-combined.bin firmware-combined.bin
```

To specify a particular version of micropython provide it through the `build-arg`. Otherwise the HEAD of the master branch will be used.

```bash
  docker build -t fancontrol-build --build-arg VERSION=v1.8.7 .
```

The firmware can then be uploaded with the esptool

```bash
  esptool.py --port ${SERIAL_PORT} --baud 115200 write_flash --verify --flash_size=detect 0 firmware-combined.bin
```

Here `${SERIAL_PORT}` is the path to the serial device on which the board is connected.

### Flash and upload from within Container

If you have built the image directly on your host (Linux), you also can flash your ESP directly by running a container from the image.
I prefereably **erase** flash memory of ESP8266 before starting flash a new firmware

```bash
docker run --rm -it --device ${SERIAL_PORT} --user root --workdir /micropython/ports/esp8266 fancontrol-build make PORT=${SERIAL_PORT} erase deploy
```

Here `${SERIAL_PORT}` is the path to the serial device on which the board is connected, generally is equal to /dev/ttyUSB0.



## Software design

~~~plantuml
```plantuml
@startuml
class MyButton {
  pressed_queue
  button_pin
  pressed
  __init__()
  check_presses()
}

class MyFan {
  wdt
  mqtt_enabled
  state
  trigger_temp
  in_pause_mode
  mqtt_password
  minor_change
  last_override
  temp
  state_text
  mqtt_topic
  led
  mqtt_username
  override_secs
  fan
  mqtt_broker
  last_major_temp
  on
  button
  __init__()
  switch_state()
  pause_temp_check()
  check_changes()
}

class MyPicoWeb {
  kwargs
  __init__()
  handle_exc()
  _handle()
}

class MyTemp {
  temp
  d
  __init__()
  read()
  refresh()
}

class WDT {
  _timeout
  _use_rtc_memory
  _timer
  _counter
  __init__()
  init()
  deinit()
  _wdt()
  feed()
}

class picoweb.WebApp {
}

class dht.DHT22 {
}

class Pin {
}

class utime.time {
}

class machine.Timer {
}

MyPicoWeb --|> picoweb.WebApp 
dht.DHT22 <-- MyTemp : dht.DHT22
Pin <-- MyFan : Pin
utime.time <-- MyFan : utime.time
machine.Timer <-- WDT : machine.Timer
@enduml
```
~~~



## Special thanks to

- Erik Wallebom for always helping with the electronic challenges
- Micropython comments in forums and good and tool like [data_to_micropython](https://github.com/peterhinch/micropython_data_to_py) by Peter Hinch
- picoweb project by Paul Sakolovsky
- Thanks to Paul Falstad for his [Circuit simulator](https://www.falstad.com/circuit/circuitjs.html)

