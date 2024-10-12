import setuptools

with open('requirements-backend.txt') as f:
    backend_requirements = f.read().splitlines()

with open('requirements-ui.txt') as f:
    ui_requirements = f.read().splitlines()

setuptools.setup(
    name='srst-groq-whisper',
    version='1.0',
    packages=setuptools.find_packages(),
    install_requires=backend_requirements + ui_requirements,
    entry_points={
        'console_scripts': [
            'srst-groq-whisper-backend=yatetradki.uitools.dictate.backend:main',
            'srst-groq-whisper-ui=yatetradki.uitools.dictate.ui:main',
        ],
    },
)
