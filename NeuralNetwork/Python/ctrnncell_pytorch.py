# -*- coding: utf-8 -*-
"""CTRNNCell.py

Pytorchに標準搭載されているRNNやLSTM等を使わず，論文等をもとに自分でRNNモジュールを作る必要がある時のお話．

結論を言ってしまえば，nn.Moduleを継承して内部構造を作ればいいだけ．

具体的に解説するためにCTRNNのモデルを実装してみる．
ちなみにMTRNNはtauの配列を二つに分けるだけ．
"""

#インポート
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

#学習用データを作る
def sin(T=100):
  x=np.arange(0,2*T+1)
  noise=np.random.normal(loc=0.0,scale=0.02,size=len(x))

  return (np.sin(2*np.pi*x/T)*0.8+noise)

data=sin()
data_length=len(data)
train_x=[]
train_t=[]
for i in range(data_length-1):
  train_x.append(data[i])
  train_t.append(data[i+1]) 
train_x=torch.Tensor(train_x)
train_t=torch.Tensor(train_t)

plt.plot(data)
plt.show()

"""ここまでは単なるインポートと学習データを作っているだけ．

学習するデータはガウスノイズの乗ったサインカーブ．

以下で実際にどう実装するかを解説していく．
"""

#活性化関数のゲインを調整しやすいように関数を作る
def Tanh(x):
  gain=1.0
  return torch.tanh(gain*x)

#CTRNNの内部構造を作る
class CTRNNCell(nn.Module):
  def __init__(self,n_in,n_hid,tau):
    super(CTRNNCell,self).__init__()
    self.i2h=nn.Linear(n_in,n_hid)
    self.h2h=nn.Linear(n_hid,n_hid)
    self.h=None
    self.tau=tau

  def reset_state(self):
    self.h=None

  def forward(self,x):
    if self.h is None:
      h_new=self.i2h(x)
    else:
      h_new=(1-1/self.tau)*self.h+(1/self.tau)*(self.i2h(x)+self.h2h(Tanh(self.h)))
    self.h=h_new
    h_out=Tanh(h_new)
    h_out=h_out.detach()

    return h_out

#実際に回すモデルを構築する
class CTRNN(nn.Module):
  def __init__(self,n_in,n_hid,n_out,tau):
    super().__init__()
    self.ctrnn=CTRNNCell(n_in,n_hid,tau)
    self.h2o=nn.Linear(n_hid,n_out)

  def reset_state(self):
    self.ctrnn.reset_state()

  def __call__(self,x,t):
    y=self.forward(x)
    mse=nn.MSELoss()
    loss=mse(y,t)
    return y,loss

  def forward(self,x):
    h=self.ctrnn(x)
    output=Tanh(self.h2o(h))

    return output

#モデルセットアップと初期設定
model=CTRNN(n_in=1,n_hid=5,n_out=1,tau=2.0)
print(model)
optimizer=optim.Adam(model.parameters(),lr=0.01)

epoch=2000
y_list=[]
loss_list=[]

#学習用ループ
for i in range(epoch):

  total_loss=0
  optimizer.zero_grad()
  model.reset_state()

  for j in range(data_length-1):
    x=torch.Tensor([[train_x[j]]])
    t=torch.Tensor([[train_t[j]]])

    y,loss=model(x,t)
    total_loss = total_loss + loss

  print('epoch:',i,'loss:',total_loss)
  loss_list.append(total_loss)

  total_loss.backward()
  optimizer.step()

#予測モード
for j in range(data_length-1):
  x=torch.Tensor([[train_x[j]]])

  if (j>=1):
    x=x*1.0+out*0.0

  out=model.forward(x)

  y_list.append(out)

#学習結果の視覚化
plt.plot(loss_list)
plt.grid(which="both")
plt.show()

plt.plot(y_list)
plt.grid(which="both")
plt.show()

