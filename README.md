# gpu-unlock-4090-windows

An experimental UEFI app that runs the Ada tensor unlock on **one exact RTX 4090 system** and then starts Windows. It is a port of the Latence.app RTX 4070 Ti Windows reference in [JustAResearcher/gpu-unlock-ada](https://github.com/JustAResearcher/gpu-unlock-ada) (`windows/ad104-msi`). The unmodified Windows NVIDIA driver loads afterwards and sees the unlocked card, so WSL2 and Docker CUDA workloads see it too.

GeForce Ada cards run FP16 and BF16 tensor math with FP32 accumulation at half the rate of FP16 accumulation. The unlock changes that limit in the card for the current power cycle. Nothing is written to the VBIOS. A full power-off returns the card to stock.

## Result on the tested system

The first hardware run (2026-10-25, log `RUN0001`) completed the transaction: preflight, display release, FWSEC, Booter and payload, both selector writes (`SS0 -> 0x88888888`, `SS1 7 -> 8`), the values held after FLR, cleanup, and Windows started by itself. The stock driver loaded normally with all 24,564 MiB.

Matched stock and unlocked runs on the same card, driver, 480 W limit, WSL2 container and scripts. The stock run was a normal boot after a full power-off; the unlocked run followed RUN0001. Each value is the median of 5 timed runs.

Register-resident tensor issue rate (Triton `tl.dot` loop, 128x128x32 tiles, operands held in registers):

| Inputs, accumulate | Stock | Unlocked | Change |
|---|---:|---:|---:|
| FP16, FP16 (control, not limited) | 226.8 | 237.9 | +5% |
| FP16, FP32 | 127.4 | **263.9** | **+107%** |
| BF16, FP32 | 139.3 | **201.8** | **+45%** |
| FP32-acc / FP16-acc ratio | 0.56 | 1.11 | |

TFLOP/s. FP16 with FP32 accumulation doubled and now runs as fast as FP16 accumulation.

Ordinary matrix multiplies (PyTorch 2.5.1 / cuBLAS, 8192x8192, reduced-precision reductions off):

| Type | Stock | Unlocked | Change |
|---|---:|---:|---:|
| BF16 | 137.6 | 143.4 | +4% |
| FP16 | 135.3 | 141.1 | +4% |
| TF32 | 69.0 | **90.8** | **+32%** |

BF16 and FP16 GEMM gained about 4%, which is within the 5% difference the unlimited control showed between the two boots, so treat it as no clear gain. TF32 gained 32%, well beyond that. The upstream matched Linux run on an RTX 4090 found FP16 cuBLAS gains of 12 to 34% depending on shape. This is one stock and one unlocked boot with short runs, not an application speedup or a long-term stability test.

## Exact profile

Tested once, on one machine:

- GPU: MSI RTX 4090 Suprim X, `10de:2684`, subsystem `1462:5102`, rev A1, VBIOS 95.02.3c.00.3c, 24,564 MiB, 480 W limit
- Board: MSI MEG Z790 GODLIKE (MS-7D85), BIOS 1.H0, Intel i9-13900K
- Windows build 26200, NVIDIA driver 617.14, Secure Boot off

Everything that matters is pinned: PCI IDs and config words, the physical ROM hash and FWSEC geometry, cold register values, the board's loaded display and input driver code (size, stop address and hash), the GOP and device paths, the five firmware asset hashes, and the Windows boot partition and boot manager. **A matching PCI ID alone is not enough.** Another RTX 4090 model, another board, a different BIOS version or a different boot partition layout is refused before anything is touched. Porting it to another system needs a new capture and review. Do not remove checks to make another system boot.

## What changed from the 4070 Ti port

- Card and chip: IDs, `PMC_BOOT_0 0x192000a1`, framebuffer `0x5ff4` MiB, MMU range, BAR3 config word, ROM hash, all taken from this card's capture.
- Cold-entry state: this card reads `SS1 = 7` at power-on (the 4070 Ti read 1). Both the profile gate and the core's cold gate require 7.
- Memory layout: computed from the card's framebuffer register, nothing hardcoded for 12 GB. On 24 GB, FRTS lands at `0x5ff200000`.
- Z790 board: the AMI text and graphics console drivers have different sizes, stop addresses and code hashes. The NVIDIA GOP sits at `_ADR 0x80010300` and creates two idle outputs (`0x80010320`, `0x80010340`) that are pinned exactly. The pointer splitter also consumes the absolute pointer protocol, with the same ownership and USB path rules as the simple pointer.
- Only `0x2684` is admitted; the 4070 Ti Super path from upstream was removed.
- Boot screen text in English; USB folders renamed `AD102-ASSETS` and `AD102-UNLOCK`.

Some internal names still say AD104 (`AD104-EXPERIMENTAL.EFI`, `GU_AD104_TRANSACTION`). They come from upstream and do not change behaviour.

## Build

Needs Windows x64, MinGW-w64 GCC with `ar` and `nm` (tested MSYS2 mingw64 GCC 13.2; some other GCC builds cannot compile the host tests because of `%zu` format checks), Python 3, and the MSVC x64 linker (tested VS 2022 Build Tools, found through `vswhere`, or pass `-VcVars64`). Building and testing never touch the GPU, the internal ESP or boot variables.

Your ESP partition GUID is kept out of Git. Create the ignored local header and put your reviewed GUID in it:

```powershell
New-Item -ItemType Directory -Force local
Copy-Item boot_profile.example.h local/boot_profile.h
# Replace the all-zero example with your ESP partition GUID.
.\Build-Experimental.ps1 -Gcc C:\msys64\mingw64\bin\gcc.exe
```

The GUID is only one of the boot checks. `boot_io.c` also requires ESP partition 1, start LBA 2048, size 204,800 sectors, and `\EFI\Microsoft\Boot\bootmgfw.efi` of 3,086,728 bytes with SHA-256 `b6f5ff8a5f605840796875259bba555d0642745a7ac8a5b38d16603768b22570`. A Windows update that replaces the boot manager makes the app refuse to start Windows (it fails safe); capture the new file and update the pin.

Output: `build/AD104-EXPERIMENTAL.EFI`. The build verifies the x64 EFI entry, relocations, no imports/TLS/CLR, and per-function stack frames. No EFI binary is distributed.

## Firmware assets and tests

No NVIDIA firmware, payload, ROM, loaded driver code or Windows binary is included. Generate the five AD102 assets with the upstream hash-pinned workflow in Linux, WSL or Docker:

```sh
# In a gpu-unlock-ada checkout at 491925c1079435e260137b9f3526066e764de830
make inputs assets CACHE=/your/private/cache ASSETS=/your/private/ad102-assets
```

`profile.c` checks their names, sizes and hashes.

The [read-only probe](diagnostic/README.md) (`AD102-PROBE.EFI`) captures your own card and board to JSON on its USB stick. It writes nothing to the GPU or the boot setup. Raw captures contain proprietary ROM and driver code: never publish them. Extract the private test inputs, then run the full simulated test set:

```powershell
python tools/extract_private_capture.py CAP0001.JSON --out local/capture
# MinGW-w64 GCC must come first on PATH for the core tests.
$env:PATH = "C:\msys64\mingw64\bin;$env:PATH"
.\Test-Experimental.ps1 -IncludeCore `
  -Prom local/capture/ad102-physical-prom.bin `
  -Assets C:\private\ad102-assets `
  -DriverCode local/capture `
  -WindowsImage C:\private\bootmgfw.efi
```

`tools/gen_capture_fixtures.py CAPTURE.JSON tests` regenerates the ownership graph and USB path fixtures from a capture. The tests simulate every GPU and EFI effect: 17 admission, 90 transaction, 15 application, 55 ownership and USB (8 of them for the Z790 idle outputs and absolute pointer), 8 boot I/O, **185 scenarios** in total.

## Running it

Use a FAT32 USB stick you control. Copy the EFI to `EFI\BOOT\BOOTX64.EFI` and the five assets to `AD102-ASSETS\`. The internal ESP, BCD and boot order stay unchanged.

1. Secure Boot must be off (the EFI is unsigned; the app refuses otherwise).
2. **Shut down fully.** A restart is refused, because the NVIDIA driver has already started the card's firmware. Power on and pick the USB stick in the boot menu (F11 on this board).
3. Press **U** once. S, Esc or 30 seconds starts normal Windows without touching the GPU.
4. The screen may stay frozen on the message while the GPU is released. Do not touch any device. If Windows is not back after 4 minutes, power off fully, wait 10 seconds, and choose Windows Boot Manager.
5. Read the log on the stick (`AD102-UNLOCK\RUNxxxx.TXT`), confirm Windows and the driver came back, then check correctness and throughput. A log line alone does not prove a gain.

The unlock lasts until the next full power-off. There is no automatic retry, no boot-variable change and no reconnect fallback.

## Risk

This is experimental and was validated on hardware exactly once. Every check runs before the first change to the GPU, and any mismatch refuses with nothing touched. After a failure past that point, the app keeps firmware-visible memory reserved, halts and asks for a full power-off. Nothing is written to the VBIOS, and full power-offs have returned the card to stock. No permanent damage has been reported for this unlock, but you run it at your own risk.

## Credits and licence

Port to the RTX 4090 Suprim X on the Z790 GODLIKE: [PantACRO4life](https://github.com/PantACRO4life).

Based on the **Latence.app** AD104/MSI Windows integration (admission profile, ownership and USB handling, tests, evidence), published through [Bizcott](https://github.com/Bizcott). Ada code and payload integration: [JustAResearcher/gpu-unlock-ada](https://github.com/JustAResearcher/gpu-unlock-ada), building on [Zagitta/gpu-unlock](https://github.com/Zagitta/gpu-unlock) and [TOTORONG/AD103_win_unlocker](https://huggingface.co/TOTORONG/AD103_win_unlocker). UEFI strategy and compatibility: [impacifist/Windows-GPU-UNLOCK](https://github.com/impacifist/Windows-GPU-UNLOCK). Pinned commits are in `provenance.json`. This is an independent port, not endorsed by any of them.

GPL-2.0-only unless a file says otherwise. Keep the [third-party notices](THIRD_PARTY_NOTICES.md), the [Windows upstream notices](UPSTREAM-WINDOWS-NOTICES.md), the EDK II licences, the MIT notices for the probe and PE validator, and all original copyright headers.
