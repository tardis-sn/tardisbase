import pytest
import numpy as np
from tardisbase.testing.regression_data.hdfwriter import HDFWriterMixin
from tardisbase.testing.regression_comparison.compare import ReferenceComparer

class MockHDF(HDFWriterMixin):
    hdf_properties = ["wavelength", "luminosity", "flux"]

    def __init__(self, wavelength, luminosity, flux):
        self.wavelength = wavelength
        self.luminosity = luminosity
        self.flux = flux

@pytest.fixture(scope="session")
def base_test_data():
    np.random.seed(42)  # Ensure reproducibility
    return {
        "wavelength": np.linspace(3000, 10000, 100),
        "luminosity": np.random.normal(1e40, 1e39, 100),
        "flux": np.random.exponential(1e-15, 100)
    }

@pytest.fixture
def reference_paths(tmp_path):
    ref1_path = tmp_path / "ref1"
    ref2_path = tmp_path / "ref2"
    ref1_path.mkdir()
    ref2_path.mkdir()
    return ref1_path, ref2_path

@pytest.fixture
def identical_hdf_files(reference_paths, base_test_data):
    ref1_path, ref2_path = reference_paths
    
    mock1 = MockHDF(**base_test_data)
    mock2 = MockHDF(**base_test_data)
    
    hdf_file1 = ref1_path / "test.h5"
    hdf_file2 = ref2_path / "test.h5"
    
    mock1.to_hdf(str(hdf_file1), path="simulation", overwrite=True)
    mock2.to_hdf(str(hdf_file2), path="simulation", overwrite=True)
    
    return ref1_path, ref2_path

@pytest.fixture
def different_hdf_files(reference_paths, base_test_data):
    ref1_path, ref2_path = reference_paths
    
    data1 = base_test_data.copy()
    data2 = base_test_data.copy()
    data2["luminosity"] = data2["luminosity"] * 1.01  # 1% difference
    
    mock1 = MockHDF(**data1)
    mock2 = MockHDF(**data2)
    
    hdf_file1 = ref1_path / "test.h5"
    hdf_file2 = ref2_path / "test.h5"
    
    mock1.to_hdf(str(hdf_file1), path="simulation", overwrite=True)
    mock2.to_hdf(str(hdf_file2), path="simulation", overwrite=True)
    
    return ref1_path, ref2_path
class TestReferenceComparerSimple:
    
    def test_identical_files_comparison(self, identical_hdf_files):
        ref1_path, ref2_path = identical_hdf_files
        
        comparer = ReferenceComparer(refpath1=ref1_path, refpath2=ref2_path)
        comparer.setup()
        comparer.compare()
        
        assert len(comparer.test_table_dict) == 1
        results = comparer.test_table_dict["test.h5"]
        assert results["identical_keys_diff_data"] == 0
        assert results["different_keys"] == 0
    
    def test_different_files_comparison(self, different_hdf_files):
        ref1_path, ref2_path = different_hdf_files
        
        comparer = ReferenceComparer(refpath1=ref1_path, refpath2=ref2_path)
        comparer.setup()
        comparer.compare()
        
        assert len(comparer.test_table_dict) == 1
        results = comparer.test_table_dict["test.h5"]
        assert results["identical_keys_diff_data"] == 1
        assert results["different_keys"] == 0
    
    def test_initialization_validation(self, reference_paths):
        ref1_path, ref2_path = reference_paths
        
        with pytest.raises(AssertionError):
            ReferenceComparer(ref1_hash="abc123", refpath1=ref1_path)
        
        with pytest.raises(AssertionError):
            ReferenceComparer()
        
        comparer = ReferenceComparer(refpath1=ref1_path, refpath2=ref2_path)
        assert comparer.using_git is False