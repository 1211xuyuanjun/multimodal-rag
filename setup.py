from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="multimodal-rag",
    version="0.1.0",
    author="1211xuyuanjun",
    author_email="101626692+1211xuyuanjun@users.noreply.github.com",
    description="基于Qwen-Agent框架的多模态检索增强生成(RAG)系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/1211xuyuanjun/multimodal-rag",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "multimodal-rag=webui:main",
        ],
    },
    include_package_data=True,
    package_data={
        "multimodal_rag": ["*.txt", "*.md"],
    },
)
