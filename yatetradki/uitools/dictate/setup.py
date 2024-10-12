import setuptools

with open('requirements-backend.txt') as f:
    backend_requirements = [line.strip() for line in f.readlines()]

with open('requirements-ui.txt') as f:
    ui_requirements = [line.strip() for line in f.readlines()]

setuptools.setup(
    name='srst-groq-whisper',
    version='1.0',
    packages=setuptools.find_packages(),
    include_package_data=True,
    package_data={
        'dictate': ['icons/*.png'],
    },
    install_requires=backend_requirements + ui_requirements,
    entry_points={
        'console_scripts': [
            'srst-groq-whisper-backend=dictate.backend:main',
            'srst-groq-whisper-ui=dictate.ui:main',
        ],
    },
    scripts=['scripts/srst-groq-whisper'],
)
