# Build Report

## Explanation

This is an automatically generated document, which contains the results of an ufotest build. A build refers to the
process of cloning the camera source code directory, flashing the new version of the configuration from the repository
to the hardware and running an automated test suite on the resulting hardware configuration.

[UfoTest](https://github.com/the16thpythonist/ufotest) is an application which aims to implement unit testing and CI
functionality for the UFO camera hardware which was developed at the IPE. The Documentation for the project can be
found here: [UfoTest Documentation](https://ufotest.readthedocs.io/en/latest/index.html).

## Build Context

The build was started at **{{ report.start }}** and ended **{{ report.end }}** with a total
duration of **{{ report.duration }}** minutes.

The build cloned the source repository at **{{ report.repository }}**. Specifically the commit **{{ report.commit }}**
from the branch **{{ report.branch }}**.

Information about this build were saved within the 'builds' folder of the ufotest application on the machine which is
currently hosting the CI server. This specific report is saved in the sub folder called **{{ report.folder }}**.
This folder also contains the *.BIT file* which was flashed to the hardware to produce these results.

## Test Results

The test suite which was executed on the camera hardware after the new version was flashed is called
**{{ report.test_suite }}**. This suite contains a total of **{{ report.test_count }}** separate test cases. The
specific names of these test cases can be seen in the separate *test report*. This test report can be found in the
**{{ report.test_report_folder }}** folder within the 'archive' folder of the ufotest installation.
The specific test report is located [HERE](../../archive/{{ report.test_report_folder }}/report.md)

A total of **{{ report.test_percentage }}%** of all test cases were successful.

## Summary

A short summary of the most important data:

- Start time: {{ report.start }}
- Duration: {{ report.duration }}
- Repository: {{ report.repository }}
- Commit: {{ report.commit }}
- Test suite: {{ report.test_suite }}
- Test success ratio: {{ report.test_percentage }} (out of {{ report.test_count }} tests)

