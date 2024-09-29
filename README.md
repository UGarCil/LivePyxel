# LivePyxel

![logo livePyxel](https://raw.githubusercontent.com/UGarCil/LivePyxel/main/icons/main_logo_long.png)
![software preview](https://raw.githubusercontent.com/UGarCil/LivePyxel/main/icons/gif_view.gif)
LivePyxel is a python-based application, designed for a fast pixel annotation of images taken directly from a webcam feed  

# TUTORIALS
- Using LivePyxel for the first time:  https://ugarcil.github.io/LivePyxel/tutorials.html

## INSTALLATION

You will need a version of python >=3.9 with the following libraries installed:  


&emsp; pyqt5  
&emsp; opencv

I recommend the use of a virtual environment. For a commercial laptop, a good choice is to use Anaconda. Install anaconda for your OS and follow the next steps:  

1. Clone the repository to your computer
2. Open Terminal OR the Anaconda Prompt, and navigate to the folder LivePyxel (if you didn't add Anaconda to the path variables, accessing it via command prompt is not available, but you can use the Anaconda Prompt).

3. Run 
    
```
    conda env create -f requirements.yaml
```
4. Once the new environment has been created, you can type 
```
    conda activate livepyxel-env
```

5. Now you can open the program by entering the measure_curves or measure_lines folder, then execute the python script:  
```
    python main.py
```

# DOCUMENTATION
You can find targeted tutorials for each submodule, and additional information in the official online docs at https://ugarcil.github.io/LivePyxel/