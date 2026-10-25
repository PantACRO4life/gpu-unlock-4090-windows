# RTX 4090 Suprim X / MSI Z790 GODLIKE port - 2026-10-25

- Retarget the read-only probe to `10de:2684` / `1462:5102` (chip `0x192000a1`) and capture the reference system (CAP0001).
- Pin the card from that capture: PCI IDs and config words (BAR3 high word `0x48`), physical ROM hash, cold registers (framebuffer `0x5ff4` MiB, MMU range), cold `SS1 = 7` in both the profile gate and the core cold gate (the 4070 Ti read 1).
- Memory layout stays computed from the framebuffer register; on 24 GB, FRTS lands at `0x5ff200000`. No 12 GB value remains in production code.
- Z790 board ownership: AMI text/graphics console driver sizes, stop addresses and code hashes; NVIDIA GOP at `_ADR 0x80010300`; the two idle NVIDIA outputs (`0x80010320`, `0x80010340`) pinned exactly; absolute pointer splitter edges under the same rules as the simple pointer.
- Windows ESP pinned to partition 1, start LBA 2048, 204,800 sectors; the boot manager size and hash are unchanged from the 4070 Ti profile.
- Admit only `0x2684`: remove the AD103 (4070 Ti Super) path and unused display-path helpers.
- English boot screen; USB folders `AD102-ASSETS` and `AD102-UNLOCK`.
- Tests ported to the capture, plus 8 new Z790 ownership cases and `tools/gen_capture_fixtures.py`: 185 simulated scenarios pass.
- First hardware run (RUN0001) completed and Windows returned. The configured public source rebuilds that EFI byte-for-byte.

# Latence.app AD104 Windows changes - 2026-10-24

- Adapt the pinned Ada transaction to checked UEFI PCI I/O, DMA and explicit error/retention state for the captured AD104 profile.
- Add MSI console/GOP ownership capture/validation and callback-based release, exclusive PCI claim and IO/MEM-only restoration.
- Preload a pinned Windows manager from a read-only ESP, require U for one attempt and contain all post-mutation failures.
- Handle periodic USB additions/removals within bounded preflight-classified USB ownership, while preserving GPU/display/console and host ownership invariants.
- Require payload marker, HALT, permission and selector/readout checks before/after one FLR; free DMA only after verified quiescence.
- Record one successful Windows handoff and three numerical/throughput runs; retain exact scope and pending A/B/A/long-duration qualification.
- Publish source-only with an ignored local ESP header, synthetic mock-test GUID, configurable compiler paths, diagnostic source and sanitized evidence. The configured public source rebuilds the historical hardware EFI byte-for-byte; 177 scenarios freshly pass.

Upstream commits and full notices remain in provenance.json and licence files. No Linux target admission changes.
