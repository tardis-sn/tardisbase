import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from _pytest.outcomes import OutcomeException

from tardisbase.testing.regression_data.hdfwriter import HDFWriterMixin


class RegressionData:
    def __init__(self, request) -> None:
        self.request = request
        if request.config.getoption("--tardis-regression-data") is None:
            pytest.skip("--tardis-regression-data was not specified")
        regression_data_path = Path(
            request.config.getoption("--tardis-regression-data")
        )
        self.regression_data_path = Path(
            os.path.expandvars(regression_data_path.expanduser())
        )
        self.enable_generate_reference = request.config.getoption(
            "--generate-reference"
        )
        self.fname = f"{self.fname_prefix}.UNKNOWN_FORMAT"
        self.hdf_store_object = None

    @property
    def module_name(self):
        return self.request.node.module.__name__

    @property
    def test_name(self):
        return self.request.node.name

    @property
    def fname_prefix(self):
        double_under = re.compile(r"[:\[\]{}]")
        no_space = re.compile(r'[,"\']')  # quotes and commas

        name = double_under.sub("__", self.test_name)
        name = no_space.sub("", name)
        return name

    @property
    def relative_regression_data_dir(self):
        relative_data_dir = Path(self.module_name.replace(".", "/"))
        if self.request.cls is not None:
            relative_data_dir /= HDFWriterMixin.convert_to_snake_case(
                self.request.cls.__name__
            )
        return relative_data_dir

    @property
    def absolute_regression_data_dir(self):
        return self.regression_data_path / self.relative_regression_data_dir

    @property
    def fpath(self):
        return self.absolute_regression_data_dir / self.fname

    def sync_dataframe(self, data, key="data"):
        """
        Synchronizes the dataframe with the regression data.

        Parameters
        ----------
        data : DataFrame
            The dataframe to be synchronized.
        key : str, optional
            The key to use for storing the dataframe in the regression data file. Defaults to "data".

        Returns
        -------
        DataFrame or None
            The synchronized dataframe if `enable_generate_reference` is `False`, otherwise `None`.
        """
        self.fname = f"{self.fname_prefix}.h5"
        if self.enable_generate_reference:
            self.fpath.parent.mkdir(parents=True, exist_ok=True)
            data.to_hdf(
                self.fpath,
                key=key,
            )
            write_status()
        else:
            return pd.read_hdf(self.fpath, key=key)

    def sync_ndarray(self, data):
        """
        Synchronizes the ndarray with the regression data.

        Parameters
        ----------
        data : ndarray
            The ndarray to be synchronized.

        Returns
        -------
        ndarray or None
            The synchronized ndarray if `enable_generate_reference` is `False`, otherwise `None`.
        """
        self.fname = f"{self.fname_prefix}.npy"
        if self.enable_generate_reference:
            self.fpath.parent.mkdir(parents=True, exist_ok=True)
            np.save(self.fpath, data)
            write_status()
        else:
            return np.load(self.fpath)

    def sync_str(self, data):
        """
        Synchronizes the string with the regression data.

        Parameters
        ----------
        data : str
            The string to be synchronized.

        Returns
        -------
        str or None
            The synchronized string if `enable_generate_reference` is `False`, otherwise `None`.
        """
        self.fname = f"{self.fname_prefix}.txt"
        if self.enable_generate_reference:
            self.fpath.parent.mkdir(parents=True, exist_ok=True)
            with self.fpath.open("w") as fh:
                fh.write(data)
            write_status()
        else:
            with self.fpath.open("r") as fh:
                return fh.read()

    def sync_hdf_store(self, tardis_module, update_fname=True):
        """
        Synchronizes the HDF store with the regression data.

        Parameters
        ----------
        tardis_module : object
            The module to be synchronized.
        update_fname : bool, optional
            Whether to update the file name. Defaults to True.

        Returns
        -------
        HDFStore or None
            The synchronized HDF store if `enable_generate_reference` is `False`, otherwise `None`.
        """
        if update_fname:
            self.fname = f"{self.fname_prefix}.h5"
        if self.enable_generate_reference:
            self.fpath.parent.mkdir(parents=True, exist_ok=True)
            with pd.HDFStore(self.fpath, mode="w") as store:
                tardis_module.to_hdf(store, overwrite=True)
            write_status()
        else:
            # since each test function has its own regression data instance
            # each test function will only have one HDFStore object
            self.hdf_store_object = pd.HDFStore(self.fpath, mode="r")
            return self.hdf_store_object


@pytest.fixture(scope="function")
def regression_data(request):
    regression_data_instance = RegressionData(request)
    yield regression_data_instance
    if (
        regression_data_instance.hdf_store_object is not None
        and regression_data_instance.hdf_store_object.is_open
    ):
        regression_data_instance.hdf_store_object.close()


class PlotDataHDF(HDFWriterMixin):
    """
    A class that writes plot data to HDF5 format using the HDFWriterMixin.
    """

    def __init__(self, **kwargs):
        """
        Initializes PlotDataHDF with arbitrary keyword arguments,
        storing them as attributes and adding their names to hdf_properties.

        Parameters:
        -----------
        **kwargs: Arbitrary keyword arguments representing properties to save.
        """
        self.hdf_properties = []
        for key, value in kwargs.items():
            setattr(self, key, value)
            self.hdf_properties.append(key)


class TestWrite(OutcomeException):
    pass


def write_status():
    raise TestWrite(msg="Writing regression data for test.")


class PytestWritingPlugin:
    def pytest_runtest_makereport(self, item, call):
        """
        Custom pytest hook to handle test report generation for regression data writing.

        This hook intercepts test execution and creates a custom test report when
        a TestWrite exception is encountered, marking the test as "written" rather
        than failed.

        Parameters
        ----------
        item : pytest.Item
            The test item being executed.
        call : pytest.CallInfo
            Information about the test call, including any exception information.

        Returns
        -------
        TestReport or None
            Returns a custom TestReport with outcome "written" if a TestWrite
            exception was raised, otherwise returns None to allow default
            report generation.

        Notes
        -----
        This hook is specifically designed for regression testing workflows where
        tests may write reference data instead of comparing against it. When a
        TestWrite exception is raised, it indicates successful data writing rather
        than a test failure.
        """
        if call.excinfo and isinstance(call.excinfo.value, TestWrite):
            from _pytest.reports import TestReport

            rep = TestReport(
                nodeid=item.nodeid,
                location=item.location,
                keywords=item.keywords,
                outcome="written",
                longrepr=None,
                when=call.when,
                sections=[],
            )
            rep.written = True
            return rep

    def pytest_report_teststatus(self, report, config):
        """
        Custom pytest hook to report test status for regression data writing.

        This hook is called by pytest to determine the test outcome status and provides
        custom reporting for tests that have written regression data.

        Parameters
        ----------
        report : pytest.TestReport
            The test report object containing information about the test execution,
            including any custom attributes set during the test run.
        config : pytest.Config
            The pytest configuration object containing command-line options and
            configuration settings.

        Returns
        -------
        tuple of (str, str, str) or None
            If the test report has a 'written' attribute that is True, returns a tuple
            containing:
            - outcome: "regression data written" (test outcome description)
            - letter: "W" (single letter representation)
            - word: "WRITTEN" (word representation for verbose output)

            Returns None if the condition is not met, allowing other hooks or default
            behavior to determine the test status.

        Notes
        -----
        This hook is typically used in conjunction with pytest plugins that handle
        regression testing data, allowing tests to be marked as having successfully
        written reference data rather than just passing or failing.
        """
        if hasattr(report, "written") and report.written:
            return ("regression data written", "W", "WRITTEN")
