"""
-------------------------------------------------------------------------------
  ***    *     *  ******   *******  ******    *****     ***    *     *  ******   
 *   *   **   **  *     *  *        *     *  *     *   *   *   **    *  *     *  
*     *  * * * *  *     *  *        *     *  *        *     *  * *   *  *     *  
*******  *  *  *  ******   ****     ******    *****   *******  *  *  *  *     *  
*     *  *     *  *        *        *   *          *  *     *  *   * *  *     *  
*     *  *     *  *        *        *    *   *     *  *     *  *    **  *     *  
*     *  *     *  *        *******  *     *   *****   *     *  *     *  ******   
-------------------------------------------------------------------------------
 * AmpersandCFD is a minimalist streamlined OpenFOAM generation tool.
 * Copyright (c) 2024 THAW TAR
 * All rights reserved.
 *
 * This software is licensed under the GNU General Public License version 3 (GPL-3.0).
 * You may obtain a copy of the license at https://www.gnu.org/licenses/gpl-3.0.en.html
 */
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# plot residuals generated by foamLog
def plot_residuals():
   # read x,y data from the file
    Ux_0 = pd.read_csv(f"log/Ux_0", sep='\\s+', header=None)
    Ux_0.columns = ['Time', 'Ux']
    Ux_0 = Ux_0.dropna()
    Uy_0 = pd.read_csv(f"log/Uy_0", sep='\\s+', header=None)
    Uy_0.columns = ['Time', 'Uy']
    Uy_0 = Ux_0.dropna()
    Uz_0 = pd.read_csv(f"log/Uz_0", sep='\\s+', header=None)
    Uz_0.columns = ['Time', 'Uz']
    Uz_0 = Uz_0.dropna()
    p_0 = pd.read_csv(f"log/p_0", sep='\\s+', header=None)
    p_0.columns = ['Time', 'p']
    p_0 = p_0.dropna()
    Ux_0.plot(x='Time', y='Ux')
    Uy_0.plot(x='Time', y='Uy')
    Uz_0.plot(x='Time', y='Uz')
    p_0.plot(x='Time', y='p')
    plt.show()

def create_gnuplot_script():
    script_content = """
set terminal pngcairo
set output 'residuals.png'
set xlabel 'Time'
set ylabel 'Residuals'
plot 'logs/Ux_0' using 1:2 with lines title 'Ux', \\
        'logs/Uy_0' using 1:2 with lines title 'Uy', \\
        'logs/Uz_0' using 1:2 with lines title 'Uz', \\
        'logs/p_0' using 1:2 with lines title 'p'
    """
    with open('plot_residuals.gnuplot', 'w') as file:
        file.write(script_content)

create_gnuplot_script()

if __name__ == '__main__':
    plot_residuals()