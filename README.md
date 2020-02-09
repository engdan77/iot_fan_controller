# Internet-Of-Things Fan Controller

[TOC]

<img src="https://docs.zerynth.com/latest/_images/nodemcu3.jpg" style="zoom:50%;" />

## Background and reflections

I noticed that my Macbook Pro became rather warm while working and thought I would drill a hole and place fan under the surface of the laptop, I also remembered I both had a few [ESP8266](https://en.wikipedia.org/wiki/ESP8266) ([NodeMCU v3](https://docs.zerynth.com/latest/official/board.zerynth.nodemcu3/docs/index.html), let's call it MCU) and [DHT22](https://www.sparkfun.com/datasheets/Sensors/Temperature/DHT22.pdf) in box somewhere to be used in some context and this was a good oportunity get use of those allowing the temperature 🌡 of the surface to control whether that fan should be on or off to avoid unnecesary noise. I first begun thinking I could spend a moment soldering the this together with a [BC547](https://en.wikipedia.org/wiki/BC548) <u>transistor</u> to allow a 3.3v from [GPIO](https://en.wikipedia.org/wiki/General-purpose_input/output) of the MCU allow a higher voltage 12v to the <u>fan</u> ♒︎. Easy-peasy.. hmm, it might also be nice to have a <u>button</u> 🔘 to be able to force an on/off so let's put there as well to another GPIO... but before trying this on a breadboard, I got caught with some fundemental trap while verifying the transistor working, and thankfully to my electronic-genius to friend [Erik](https://www.linkedin.com/in/erik-wallebom-240792178) helped me get it right.. Now next soldering .. and a lot of cursing - honestly it must be difficult finding anyone worse than me soldering but finally those pieces in its place and now to the part I find most fun, programming Micropython to do the work for me.
With a few lines of code l just doing a quick while-loop to determine the temperatur and supply voltage to a GPIO was extremely easy, but it made me think bigger .. wouldn't it be nice to have a [RESTful-API](https://en.wikipedia.org/wiki/Representational_state_transfer) to allow me to control this fan through the <u>network</u> ...? Well, that in itself is easily done .. now, the challenge here is concurrency - we do need to assure we maintain the state of the button, and the temperature at the same time as we need to assure that the MCU also responds to incoming TCP/IP packets the code needs to following [asynchronous paradigm](https://en.wikipedia.org/wiki/Asynchrony_(computer_programming)) due to the fact that this is a single-core RISC-processor without support for threading. 🤔 Thankfully Micropython does support asyncio that makes this possible by async/await keywords. To save some efforts writing the web-framework I found this nice [picoweb](https://github.com/pfalcon/picoweb) to the rescue built as async. Now for readability I developed classes for button-presses and temperature with builtin subroutines checking their states, now exposing these to the web-framework there was a need to subclass a couple of methods to allow this.... now almost there ... now I was able to use REST to also check status and also suppled methods to update configuration... hmm .. wouldn't it be even nicer to build a [captive portal](https://en.wikipedia.org/wiki/Captive_portal) 📲 that many products does have to simplify configuration, I went into the rabbit-hole learning everything about captive portals that involves quite a lot of spoofing-mechanism not only involving HTTP, DHCP but also DNS-requests .. I found some projects built trying this out, but didn't find it stable enough so I left this with some better insight of this for the future. I did manage to supply code that allows the MCU to broadcast an essid "fan_control" that allows one to access if the Wifi configured is not properly connected - this is allows me to alway configure the device if Wifi isn't working.The captive portal gave me the idea that it would also be nice to have some sort of a <u>web-configuration-interface</u>  for the initial configuration instead of hard-code configuration or send as REST (JSON) .. found some boilerplate for that but now I dug deeper into the world of CSS to make it look nice, [AJAX](https://en.wikipedia.org/wiki/Ajax_(programming)) using [JQuery](https://en.wikipedia.org/wiki/JQuery) to allow me to nicely have the web-interface with help of my REST-API in real-time (or near) present the state of the fan and what the current temperature is. With this interface you could also configure Wifi-settings ... now since I am happy user of the great Home Assistant (HASS) project where its heart of home-automation is an MQTT-broker, I also thought that I might as well add [MQTT](https://en.wikipedia.org/wiki/MQTT)-client to allow this MCU to inform my HASS what the temperature currently is... That's cool, that way I can e.g. have the home inform me by shouting to me through the SONOS-speakers when my laptop burns in flames 🔥 😜 .. Ok, cool .. now while squeezing more and more Python-code while the project grew successfully it finally more and more often got something like.. 

```
MemoryError: memory allocation failed, allocating 4084 bytes
```

 Oh dear ... now what can one expect from a such small device with a cost equallent to a chocolate-cake .. I read and learned that NodeMCU v3 in particular has 4MB flash, which is the "permanent" storage which is quite a lot, but now it turns out that <u>this MCU has roughly 50KB of usable RAM to use</u> (in fact see like 21KB after [REPL](https://docs.micropython.org/en/latest/esp8266/tutorial/repl.html) been started)  .. Slightly less than Commode 64 😂 so quite impressive that you can really do this much with that little memory. I've learnt that one could save memory by [freezing](http://docs.micropython.org/en/v1.9.3/unix/reference/constrained.html) ❄️ your modules into byte-code *(as you may know Micropython does a compilation before you run the code)*, and you do this by adding those **.py** file into the "modules" folder before compiling a binary you can upload to the MCU, there was also another lesson learned that to allow Micropython to address all of those 4MB flash you would need to configre it to do so instead of those defaul 512KB flash that the even slimmer/cheaper models ESP-01 does have.. this was described in this [thread](https://github.com/micropython/micropython/issues/2700#issuecomment-287737238). Now also thanks to docker-images such as [this](https://hub.docker.com/r/fcollova/micropython-docker-build/) one made it easy to build your own image without the hassle of configuring the cross-compiler. Now since it is better being safe than sorry, even though since I've build a frozen code saving RAM and yet no memory allocation failures it turns out that one could easily implement a [Watch Dog Timer](https://en.wikipedia.org/wiki/Watchdog_timer) 🐕 that make sure that assure that in case of a larger exception we have an interrupt that assures the MCU resets itself... and now if MQTT is being enabled one would easily get informed when this happens.

Now .. finally, with a binary-image of less than **610KB** uploaded to the MCU it now supports

- [x] Fan control by
  - [x] Temperatures based on under/above threshold
  - [x] Button clicks
  - [x] REST-API
  - [x] Web-interface
- [x] Temperatue readings by
  - [x] Web-interface
  - [x] Push to MQTT-queue
- [x] Configuration by
  - [x] Web-interface
  - [x] REST-API
- [x] Watch Dog in case of unpredictable errors

All coded in concurrent-fashion ... and now with the cost around a couple of Euros .. Cool 😁👍🏻



## Build a frozen image and upload to ESP8266

### Manually bild binary image without upload

Build the docker image of the master branch. The custom Dockerfile will add src as frozen and update the entrypoint

```bash
  docker build -t fancontrol-build .
```

To specify a particular version of micropython provide it through the `build-arg`. Otherwise the HEAD of the master branch will be used.

```bash
  docker build -t fancontrol-build --build-arg VERSION=v1.8.7 .
```


Once the container is built successfuly create a container from the image

```bash
  docker create --name fancontrol-build fancontrol-build-container
```

Then copy the the built firmware into the host machine.

```bash
  docker cp fancontrol-build-container:/micropython/ports/esp8266/build-GENERIC/firmware-combined.bin firmware-combined.bin
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



## Special thanks to

- Erik Wallebom for always helping with the electronic challenges
- Micropython comments in forums and good and tool like [data_to_micropython](https://github.com/peterhinch/micropython_data_to_py) by Peter Hinch
- picoweb project by Paul Sakolovsky

