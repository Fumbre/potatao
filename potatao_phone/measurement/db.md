# Memory Profile: MicroPython `usqlite` & SD Card Storage

This document tracks the RAM consumption profiles of `usqlite` combined with an SPI SD Card File System (`os.VfsFat`) on a MicroPython microcontroller. 

## Summary Matrix

| Test Scenario | Isolated Phase Description | RAM Used (Bytes) | RAM Used (KB) | Remaining Free RAM |
| :--- | :--- | :---: | :---: | :---: |
| **1. Full Lifecycle** | Complete run (Hardware SPI + SD Mount + DB Create + Query) | 75,472 B | ~73.70 KB | 366,944 B |
| **2. DB Fresh Setup** | DB Creation + Data Structural Seed + Query Execution | 68,848 B | ~67.23 KB | 372,320 B |
| **3. DB Cached Open** | Connection open to an already existing file + Query | 26,656 B | ~26.03 KB | 414,528 B |
| **4. Raw Query Only**| Pure `SELECT` execution & fetching results to tuple array | 7,168 B | ~7.00 KB | 421,520 B |

---

## Detailed Scenario Breakdown

### Test 1: Full System Lifecycle
* **Measurement Scope:** From the absolute start of script initialization (pre-hardware allocation) up to right before `db.close()`.
* **RAM Used:** `75,472 bytes` (~73.70 KB)
* **System Impact:** This captures the heaviest operational "high-water mark." It accounts for importing modules, starting the hardware `SPI(1)` engine, initializing the `sdcard.SDCard` driver class, mounting the internal FAT table tracking, building dynamic raw string statements for insertion, and keeping the database handle open concurrently.

### Test 2: Database Initialization & Seeding (Fresh Start)
* **Measurement Scope:** Triggered *after* `os.remove()` wiping the old file, measuring the connection window, building table definitions via `db_create()`, running multi-statement batch strings inside `executemany`, and pulling the initial UI layout.
* **RAM Used:** `68,848 bytes` (~67.23 KB)
* **System Impact:** This proves that generating dynamic SQL transaction blocks (`INSERT INTO ...`) inside memory loops demands a temporary peak of RAM. This is your maximum computational expense during a "Factory Reset" or application update phase.

### Test 3: Active File Hooking (Normal Sub-sequent Boot)
* **Measurement Scope:** The database already exists on the SD Card (`db_exist` returns true). Measures the connection hook step and running the check query.
* **RAM Used:** `26,656 bytes` (~26.03 KB)
* **System Impact:** Significantly lighter! Skipping the string allocation overhead of parsing structure setups saves roughly **~41.2 KB** of heap space. This represents what your phone interface initialization cost will look like during ordinary power-up sequences.

### Test 4: Isolated Data Query Execution
* **Measurement Scope:** `gc.collect()` triggered directly right before calling `.execute()`, isolating *only* the query cycle and the tuple storage buffer mapping.
* **RAM Used:** `7,168 bytes` (~7.00 KB)
* **System Impact:** Microscopic. This shows that the active `usqlite` execution engine and row-fetching mechanics are highly optimized. Reading menus dynamically on demand while the phone interface is running will only ever cost a tiny **7 KB fraction** of the MicroPython Heap.

---

## Technical Insights & Takeaways

1. **`usqlite` Allocation Characteristics:**
   The native internal tracking wrappers consistently read `usqlite mem - current: 0 peak: 0`. This implies that SQLite relies directly on the underlying core MicroPython Heap structure rather than spinning off its own dedicated custom C-level `malloc` memory arenas.
   
2. **The SD Card Drivers "Tax":**
   Subtracting Test 2 from Test 1 shows us that initializing the basic hardware state and mounting an active FAT partition claims an immutable block of around **6.6 KB** of permanent system memory.

3. **Optimizing Operational Flow:**
   Because running queries dynamically is so cheap (Test 4: 7 KB), you do not need to read the entire database into memory arrays on startup. You can safely keep the DB connection active or flip it open/closed seamlessly on UI menu changes without starving the application runtime heap.


```
import usqlite
import sdcard

from libs.conf.pins import PIN_SDCARD_CLK, PIN_SDCARD_MOSI, PIN_SDCARD_MISO, PIN_SDCARD_CS
from libs.db.db import db_create, db_exist

import gc
import os

from machine import Pin, SPI

# TODO: 
# - make a setup function for every setup

# Force a garbage collection so we get a clean baseline
gc.collect()
mem_before = gc.mem_free()


# SD setup
spi = SPI(1, baudrate=10_000_000, sck=Pin(PIN_SDCARD_CLK), mosi=Pin(PIN_SDCARD_MOSI), miso=Pin(PIN_SDCARD_MISO))
sd = sdcard.SDCard(spi, Pin(PIN_SDCARD_CS))
vfs = os.VfsFat(sd)
os.mount(vfs, "/sd")

# os.remove("/sd/potatao.db")


# db setup
if not usqlite.mem_status():
    usqlite.mem_status(True)
    
db = usqlite.connect("/sd/potatao.db")
if not db_exist(db):
    db_create(db)
else:
    print("Database already exists, skipping setup")




# verify
rows = db.execute("SELECT * FROM potatao_ui WHERE parent_id=0").fetchall()
print("Main menu items:", rows)

print("usqlite mem - current:", usqlite.mem_current(), "peak:", usqlite.mem_peak())


mem_after = gc.mem_free()
print(f"MicroPython RAM used by query: {mem_before - mem_after} bytes")
print(f"Total Free MicroPython RAM: {mem_after} bytes")

db.close()




os.umount("/sd")
```