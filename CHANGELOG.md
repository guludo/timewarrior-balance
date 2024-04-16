# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## Unreleased
### Added
- Added support for specifying exceptions in periodic blocks via the `except`
  keyword. See the README for details.

### Fixed
- Rounding datetimes is performed only when the time component is not already
  midnight in local timezone.
- Total row was not being generated when the report interval does not match any
  data or configuration entry, which caused an exception to be thrown. The bug
  was fixed by always initializing the total accumulators.


## 0.2.1 - 2022-05-16
### Fixed
- When calculating allotted time, the `round_interval` configuration was not
  being taken into account and that led to buggy behavior. That has been fixed
  now.


## 0.2.0 - 2022-05-14
### BREAKING CHANGES
- Intervals for the report are rounded such that the time for the start date
  is set to 0:00:00 and the end timedate is set to next day at 0:00:00. This
  provides a less confusing behavior for the user (see
  https://github.com/guludo/timewarrior-balance/issues/3). Previous behavior
  can be restored by using `round_interval = false` in the configuration file.

### Fixed
- Fixed the fix from `0.1.1`: when negative minutes did not amount to at last
  one hour, they where formatted as if they where positive, for example: `-41`
  would be formatted as `+0:41`. Hopefully we really fixed the issue now.
- Tags described as strings in the configuration would have the first and last
  characters because of a bug. That has been fixed.


## 0.1.1 - 2021-10-22
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
  , where the balance should actually be `-16:01`. This is fixed now.


## 0.1.0
### Added
- First release!
