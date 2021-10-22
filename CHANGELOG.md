# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## Unreleased
### Fixed
- Fixed bad rounding for negative deltas. Before this fix we would run into
  the following situation:
  ```
  Start: Tue Jan  2 00:00:00 0001
    End: Fri Oct 22 08:43:56 2021

    Tag   Spent  Allotted  Balance
  ────────────────────────────────
    xyz  103:59    120:00   -17:01
  ```
  , where the balance should actually be `16:01`. This is fixed now.


## 0.1.0
### Added
- First release!
