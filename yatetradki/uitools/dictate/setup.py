import setuptools

setuptools.setup(
    name='srst-groq-whisper',
    version='1.0',
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'srst-groq-whisper-backend=yatetradki.uitools.dictate.backend:main',
            'srst-groq-whisper-ui=yatetradki.uitools.dictate.ui:main',
        ],
    },
)
