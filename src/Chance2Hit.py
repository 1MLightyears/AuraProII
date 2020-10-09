#计算命中率，绘制命中率三维图。

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

def c2h(angular,tracking,signature,distance,optimal,falloff):
    """
    计算命中率。
    角速度/跟踪速度/信号半径/距离/最佳射程/失准射程.
    """
    return 0.5**((angular*40000/tracking/signature)**2+(max(0,distance-optimal)/falloff)**2)

def plotT(tracking,signature,optimal,falloff):
    fig = plt.figure()
    ax = Axes3D(fig)

    x=np.linspace(0,optimal+falloff*2,100)
    a=np.linspace(0,0.5,100)
    z=np.ndarray((len(x),len(a)),dtype=np.float64)
    m,n=0,0
    for i in x:
        for j in a:
            z[m,n]=c2h(j,tracking,signature,i,optimal,falloff)*100
            m+=1
        m,n=0,n+1
    #决定横纵坐标范围
    x_limit,a_limit=0,0
    for i in range(len(x)):
        if z[0,i]<1:
            x_limit=i+1
            break
        for j in range(len(a)):
            if z[j,i]<1:
                a_limit=max(a_limit,j+1)
                break
    if x_limit == 0:
        x_limit = len(x)
    if a_limit == 0:
        a_limit = len(a)
    x,a=np.meshgrid(x[0:x_limit],a[0:a_limit])
    z=z[0:a_limit,0:x_limit]
    ax.plot_surface(x, a, z, cmap=plt.cm.RdYlGn)
    plt.xlabel("m")
    plt.ylabel("angular speed(0~%.3f)"%a[-1,-1])
    ax.set_zlabel("%")
    ax.set_zlim(0,100)

    #加标签

    plt.grid()
    plt.show()

def plotM(r,v):
    """
    计算导弹爆炸伤害。
    r(float):导弹爆炸半径。
    v(float):导弹爆炸速度。

    TODO:未完成:drf部分
    https://wiki.eveuniversity.org/Missile_mechanics
    """
    fig = plt.figure()
    ax = Axes3D(fig)

    x=np.linspace(0,optimal+falloff*2,100)
    a=np.linspace(0,0.5,100)
    z=np.ndarray((len(x),len(a)),dtype=np.float64)
    m,n=0,0
    for i in x:
        for j in a:
            z[m,n]=c2h(j,tracking,signature,i,optimal,falloff)*100
            m+=1
        m,n=0,n+1
    #决定横纵坐标范围
    x_limit,a_limit=0,0
    for i in range(len(x)):
        if z[0,i]<1:
            x_limit=i+1
            break
        for j in range(len(a)):
            if z[j,i]<1:
                a_limit=max(a_limit,j+1)
                break
    if x_limit == 0:
        x_limit = len(x)
    if a_limit == 0:
        a_limit = len(a)
    x,a=np.meshgrid(x[0:x_limit],a[0:a_limit])
    z=z[0:a_limit,0:x_limit]
    ax.plot_surface(x, a, z, cmap=plt.cm.RdYlGn)
    plt.xlabel("m")
    plt.ylabel("angular speed(0~%.3f)"%a[-1,-1])
    ax.set_zlabel("%")
    ax.set_zlim(0,100)

    #加标签

    plt.grid()
    plt.show()


if __name__=="__main__":
    angular=float(input("角速度="))
    tracking=float(input("炮台跟踪速度="))
    signature=float(input("目标信号半径(mm)="))
    distance=float(input("距离(m)="))
    optimal=float(input("最佳射程(m)="))
    falloff=float(input("失准距离(m)="))
    print("命中率=",int(c2h(angular,tracking,signature,distance,optimal,falloff)*10000)/100,"%",sep="")

