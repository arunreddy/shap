from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext as _build_ext
import os
import re
import codecs

# to publish use:
# > python setup.py sdist bdist_wheel upload
# which depends on ~/.pypirc

here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

# Extend the default build_ext class to bootstrap numpy installation
# that are needed to build C extensions.
# see https://stackoverflow.com/questions/19919905/how-to-bootstrap-numpy-installation-in-setup-py
class build_ext(_build_ext):
    def finalize_options(self):
        _build_ext.finalize_options(self)
        if isinstance(__builtins__, dict):
            __builtins__["__NUMPY_SETUP__"] = False
        else:
            setattr(__builtins__, "__NUMPY_SETUP__", False)
        import numpy
        print("numpy.get_include()", numpy.get_include())
        self.include_dirs.append(numpy.get_include())


def run_setup(with_binary=True, test_xgboost=True, test_lightgbm=True):
    ext_modules = []
    if with_binary:
        ext_modules.append(
            Extension('shap._cext', sources=['shap/_cext.cc'])
        )

    if test_xgboost and test_lightgbm:
        tests_require = ['nose', 'xgboost', 'lightgbm']
    elif test_xgboost:
        tests_require = ['nose', 'xgboost']
    elif test_lightgbm:
        tests_require = ['nose', 'lightgbm']
    else:
        tests_require = ['nose']

    setup(
        name='shap',
        version=find_version("shap", "__init__.py"),
        description='A unified approach to explain the output of any machine learning model.',
        long_description="SHAP (SHapley Additive exPlanations) is a unified approach to explain the output of " + \
                         "any machine learning model. SHAP connects game theory with local explanations, uniting " + \
                         "several previous methods and representing the only possible consistent and locally accurate " + \
                         "additive feature attribution method based on expectations.",
        long_description_content_type="text/markdown",
        url='http://github.com/slundberg/shap',
        author='Scott Lundberg',
        author_email='slund1@cs.washington.edu',
        license='MIT',
        packages=[
            'shap', 'shap.explainers', 'shap.explainers.other', 'shap.explainers.deep',
            'shap.plots', 'shap.benchmark'
        ],
        package_data={'shap': ['plots/resources/*', 'tree_shap.h']},
        cmdclass={'build_ext': build_ext},
        setup_requires=['numpy'],
        install_requires=['numpy', 'scipy', 'scikit-learn', 'matplotlib', 'pandas', 'tqdm', 'ipython'],
        test_suite='nose.collector',
        tests_require=tests_require,
        ext_modules=ext_modules,
        zip_safe=False
    )


def try_run_setup(**kwargs):
    """ Fails gracefully when various install steps don't work.
    """

    try:
        run_setup(**kwargs)
    except Exception as e:
        print(str(e))
        if "xgboost" in str(e).lower():
            kwargs["test_xgboost"] = False
            print("Couldn't install XGBoost for testing!")
            try_run_setup(**kwargs)
        elif "lightgbm" in str(e).lower():
            kwargs["test_lightgbm"] = False
            print("Couldn't install LightGBM for testing!")
            try_run_setup(**kwargs)
        elif kwargs["with_binary"]:
            kwargs["with_binary"] = False
            print("WARNING: The C extension could not be compiled, sklearn tree models not supported.")
            try_run_setup(**kwargs)
        else:
            print("ERROR: Failed to build!")

# we seem to need this import guard for appveyor
if __name__ == "__main__":
    try_run_setup(with_binary=True, test_xgboost=True, test_lightgbm=True)
