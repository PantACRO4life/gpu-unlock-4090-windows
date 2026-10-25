# Read-only AD102 UEFI probe

v0.4 diagnostic source, retargeted to the RTX 4090 Suprim X (`10de:2684`, subsystem `1462:5102`, chip `0x192000a1`) and used to capture the MSI Z790 GODLIKE reference system (CAP0001). The original probe targeted the AD104 4070 Ti. It reads PCI configuration, bounded PROM/register data, paths, protocol ownership and selected loaded driver code. It writes JSON to its own USB only; it does not unlock, write GPU MMIO, change BME, release graphics drivers or edit boot variables.

Build using `Build.ps1 -Python python -VcVars <path-to-vcvars64.bat>`. Output: `build/AD102-PROBE.EFI`. A new build manifest is not hardware qualification. Preserve previous USB boot files before manually deploying a reviewed probe. No formatter/automatic installer is provided.

Captures contain full proprietary ROM/loaded code and local details. Do not commit or publish raw captures. The parent port's `tools/extract_private_capture.py` extracts matching private test inputs. Other code/ROM profiles require separate review, not a bypassed check.

MIT licence in `LICENSE.txt`; EDK II and related notices in `THIRD_PARTY.md`. PE-validator copyright/licence remains in its source.
