from casadi import *
import casadi as c
from numpy import *
import unittest
from types import *
from helpers import *

class ADtests(casadiTestCase):

  def setUp(self):
    x=SX("x")
    y=SX("y")
    z=SX("z")
    w=SX("w")
    
    out=SXMatrix(6,1)
    out[0,0]=x
    out[2,0]=x+2*y**2
    out[4,0]=x+2*y**3+3*z**4
    out[5,0]=w

    inp=SXMatrix(6,1)
    inp[0,0]=x
    inp[2,0]=y
    inp[4,0]=z
    inp[5,0]=w
    
    sp = CRSSparsity(6,1,[0, 0, 0, 0],[0, 1, 1, 2, 2, 3, 4])
    spT = CRSSparsity(1,6,[0, 2, 4, 5],[0, 4])
    
    self.sxinputs = {
       "column" : {
            "dense": [[x,y,z,w]],
            "sparse": [inp] }
        , "row": {
            "dense":  [SXMatrix([x,y,z,w]).T],
            "sparse": [inp.T]
       }, "matrix": {
          "dense": [c.reshape(SXMatrix([x,y,z,w]),2,2)],
          "sparse": [c.reshape(inp,3,2)]
        }
    }

    self.mxinputs = {
       "column" : {
            "dense": [MX("xyzw",4,1)],
            "sparse": [MX("xyzw",sp)]
        },
        "row" : {
            "dense": [MX("xyzw",1,4)],
            "sparse": [MX("xyzw",spT)]
        } 
       
    }
    
    def temp1(xyz):
      X=MX(6,1)
      X[0,0]=xyz[0]
      X[2,0]=xyz[0]+2*xyz[1]**2
      X[4,0]=xyz[0]+2*xyz[1]**3+3*xyz[2]**4
      X[5,0]=xyz[3]
      return [X]
    
    def temp2(xyz):
      X=MX(1,6)
      X[0,0]=xyz[0]
      X[0,2]=xyz[0]+2*xyz[1]**2
      X[0,4]=xyz[0]+2*xyz[1]**3+3*xyz[2]**4
      X[0,5]=xyz[3]
      return [X]
      
    self.mxoutputs = {
       "column": {
        "dense":  lambda xyz: [vertcat([xyz[0],xyz[0]+2*xyz[1]**2,xyz[0]+2*xyz[1]**3+3*xyz[2]**4,xyz[3]])],
        "sparse": temp1
        }, "row": {
        "dense": lambda xyz: [horzcat([xyz[0],xyz[0]+2*xyz[1]**2,xyz[0]+2*xyz[1]**3+3*xyz[2]**4,xyz[3]])],
        "sparse": temp2
       },
       "matrix": {
          "dense":  lambda xyz: [c.reshape(vertcat([xyz[0],xyz[0]+2*xyz[1]**2,xyz[0]+2*xyz[1]**3+3*xyz[2]**4,xyz[3]])[0],(2,2))],
          "sparse": lambda xyz: [c.reshape(temp1(xyz)[0],(3,2))]
       }
    }


    self.sxoutputs = {
       "column": {
        "dense": [[x,x+2*y**2,x+2*y**3+3*z**4,w]],
        "sparse": [out]
        }, "row": {
          "dense":  [SXMatrix([x,x+2*y**2,x+2*y**3+3*z**4,w]).T],
          "sparse": [out.T]
      }, "matrix" : {
          "dense":  [c.reshape(SXMatrix([x,x+2*y**2,x+2*y**3+3*z**4,w]),2,2)],
          "sparse": [c.reshape(out,3,2)]
      }
    }
    
    self.jacobians = {
      "dense" : {
        "dense" : lambda x,y,z,w: array([[1,0,0,0],[1,4*y,0,0],[1,6*y**2,12*z**3,0],[0,0,0,1]]),
        "sparse" : lambda x,y,z,w: array([[1,0,0,0],[0,0,0,0],[1,4*y,0,0],[0,0,0,0],[1,6*y**2,12*z**3,0],[0,0,0,1]])
        }
      ,
      "sparse" : {
        "dense" : lambda x,y,z,w: array([[1,0,0,0,0,0],[1,0,4*y,0,0,0],[1,0,6*y**2,0,12*z**3,0],[0,0,0,0,0,1]]),
        "sparse" : lambda x,y,z,w:  array([[1,0,0,0,0,0],[0,0,0,0,0,0],[1,0,4*y,0,0,0],[0,0,0,0,0,0],[1,0,6*y**2,0,12*z**3,0],[0,0,0,0,0,1]])
      }
    }
  
  
  def test_fwd(self):
    n=array([1.2,2.3,7,1.4])
    for inputshape in ["column","row","matrix"]:
      for outputshape in ["column","row","matrix"]:
        for inputtype in ["sparse","dense"]:
          for outputtype in ["sparse","dense"]:
            self.message("fwd AD on SX. Input %s %s, Output %s %s" % (inputtype,inputshape,outputtype,outputshape) )
            f=SXFunction(self.sxinputs[inputshape][inputtype],self.sxoutputs[outputshape][outputtype])
            f.init()
            f.input().set(n)
            self.assertEqual(f.fwdSeed().shape,f.input().shape,"fwdSeed shape")
            self.assertEqual(f.fwdSeed().size(),f.input().size(),"fwdSeed shape")
            J = self.jacobians[inputtype][outputtype](*n)
            for d in [array([1,0,0,0]),array([0,2,0,0]),array([1.2,4.8,7.9,4.6])]:
              f.fwdSeed().set(d)
              f.evaluate(1,0)
              seed = array(f.fwdSeed()).ravel()
              sens = array(f.fwdSens()).ravel()
              self.checkarray(sens,dot(J,seed),"AD")

  def test_adj(self):
    n=array([1.2,2.3,7,1.4])
    for inputshape in ["column","row","matrix"]:
      for outputshape in ["column","row","matrix"]:
        for inputtype in ["sparse","dense"]:
          for outputtype in ["sparse","dense"]:
            self.message("adj AD on SX. Input %s %s, Output %s %s" % (inputtype,inputshape,outputtype,outputshape) )
            f=SXFunction(self.sxinputs[inputshape][inputtype],self.sxoutputs[outputshape][outputtype])
            f.init()
            f.input().set(n)
            self.assertEqual(f.adjSeed().shape,f.output().shape,"adjSeed shape")
            self.assertEqual(f.adjSeed().size(),f.output().size(),"adjSeed shape")
            J = self.jacobians[inputtype][outputtype](*n)
            for d in [array([1,0,0,0]),array([0,2,0,0]),array([1.2,4.8,7.9,4.7])]:
              f.adjSeed().set(d)
              f.evaluate(0,1)
              seed = array(f.adjSeed()).ravel()
              sens = array(f.adjSens()).ravel()
              self.checkarray(sens,dot(J.T,seed),"AD")

  def test_fwdMX(self):
    n=array([1.2,2.3,7,1.4])
    for inputshape in ["column","row"]:
      for outputshape in ["column","row"]:
        for inputtype in ["dense","sparse"]:
          for outputtype in ["dense","sparse"]:
            self.message("fwd AD on MX. Input %s %s, Output %s %s" % (inputtype,inputshape,outputtype,outputshape) )
            f=MXFunction(self.mxinputs[inputshape][inputtype],self.mxoutputs[outputshape][outputtype](self.mxinputs[inputshape][inputtype][0]))
            f.init()
            f.input().set(n)
            self.assertEqual(f.fwdSeed().shape,f.input().shape,"fwdSeed shape")
            self.assertEqual(f.fwdSeed().size(),f.input().size(),"fwdSeed shape")
            J = self.jacobians[inputtype][outputtype](*n)
            for d in [array([1,0,0,0]),array([0,2,0,0]),array([1.2,4.8,7.9,4.6])]:
              f.fwdSeed().set(d)
              f.evaluate(1,0)
              seed = array(f.fwdSeed()).ravel()
              sens = array(f.fwdSens()).ravel()
              self.checkarray(sens,dot(J,seed),"AD")    

  def test_adjMX(self):
    n=array([1.2,2.3,7,1.4])
    for inputshape in ["column","row"]:
      for outputshape in ["column","row"]:
        for inputtype in ["dense","sparse"]:
          for outputtype in ["dense","sparse"]:
            self.message("adj AD on MX. Input %s %s, Output %s %s" % (inputtype,inputshape,outputtype,outputshape) )
            f=MXFunction(self.mxinputs[inputshape][inputtype],self.mxoutputs[outputshape][outputtype](self.mxinputs[inputshape][inputtype][0]))
            f.init()
            f.input().set(n)
            self.assertEqual(f.adjSeed().shape,f.output().shape,"adjSeed shape")
            self.assertEqual(f.adjSeed().size(),f.output().size(),"adjSeed shape")
            J = self.jacobians[inputtype][outputtype](*n)
            for d in [array([1,0,0,0]),array([0,2,0,0]),array([1.2,4.8,7.9,4.3])]:
              f.adjSeed().set(d)
              f.evaluate(0,1)
              seed = array(f.adjSeed()).ravel()
              sens = array(f.adjSens()).ravel()
              self.checkarray(sens,dot(J.T,seed),"AD")
              
  def test_Jacobian(self):
    n=array([1.2,2.3,7,4.6])
    for inputshape in ["column","row","matrix"]:
      for outputshape in ["column","row","matrix"]:
        for inputtype in ["dense","sparse"]:
          for outputtype in ["dense","sparse"]:
            for mode in ["forward","adjoint"]:
              self.message(" %s Jacobian on SX. Input %s %s, Output %s %s" % (mode,inputtype,inputshape,outputtype,outputshape) )
              f=SXFunction(self.sxinputs[inputshape][inputtype],self.sxoutputs[outputshape][outputtype])
              f.init()
              Jf=Jacobian(f,0,0)
              Jf.setOption("ad_mode",mode)
              Jf.init()
              Jf.input().set(n)
              Jf.evaluate()
              J = self.jacobians[inputtype][outputtype](*n)
              self.checkarray(array(Jf.output()),J,"Jacobian")
              
  def test_jacobian(self):
    n=array([1.2,2.3,7,4.6])
    for inputshape in ["column","row","matrix"]:
      for outputshape in ["column","row","matrix"]:
        for inputtype in ["dense"]:
          for outputtype in ["dense"]:
            self.message("jacobian on SX (SCT). Input %s %s, Output %s %s" % (inputtype,inputshape,outputtype,outputshape) )
            f=SXFunction(self.sxinputs[inputshape][inputtype],self.sxoutputs[outputshape][outputtype])
            f.init()
            Jf=f.jacobian(0,0)
            Jf.init()
            Jf.input().set(n)
            Jf.evaluate()
            J = self.jacobians[inputtype][outputtype](*n)
            self.checkarray(array(Jf.output()),J,"Jacobian")
              
  def test_JacobianMX(self):
    n=array([1.2,2.3,7,4.6])
    for inputshape in ["column","row"]:
      for outputshape in ["column","row"]:
        for inputtype in ["dense","sparse"]:
          for outputtype in ["dense","sparse"]:
            for mode in ["forward","adjoint"]:
              self.message("adj AD on MX. Input %s %s, Output %s %s" % (inputtype,inputshape,outputtype,outputshape) )
              f=MXFunction(self.mxinputs[inputshape][inputtype],self.mxoutputs[outputshape][outputtype](self.mxinputs[inputshape][inputtype][0]))
              f.init()
              Jf=Jacobian(f,0,0)
              Jf.setOption("ad_mode",mode)
              Jf.init()
              Jf.input().set(n)
              Jf.evaluate()
              J = self.jacobians[inputtype][outputtype](*n)
              self.checkarray(Jf.output(),J,"Jacobian")

  def test_jacobianMX(self):
    n=array([1.2,2.3,7,4.6])
    for inputshape in ["column"]:
      for outputshape in ["column"]:
        for inputtype in ["dense"]:
          for outputtype in ["dense"]:
            for mode in ["forward","adjoint"]:
              self.message(" %s jacobian on MX (SCT). Input %s %s, Output %s %s" % (mode,inputtype,inputshape,outputtype,outputshape) )
              f=MXFunction(self.mxinputs[inputshape][inputtype],self.mxoutputs[outputshape][outputtype](self.mxinputs[inputshape][inputtype][0]))
              f.init()
              Jf=MXFunction(self.mxinputs[inputshape][inputtype],[f.jac(0)[0]])
              Jf.init()
              Jf.input().set(n)
              Jf.evaluate()
              J = self.jacobians[inputtype][outputtype](*n)
              self.checkarray(array(Jf.output()),J,"jacobian")
              
  def test_hessian(self):
    #return # not working
    self.message("Jacobian chaining")
    x=SX("x")
    y=SX("y")
    z=SX("z")
    n=array([1.2,2.3,7])
    f=SXFunction([[x,y,z]],[[x+2*y**3+3*z**4]])
    f.init()
    J=Jacobian(f,0,0)
    J.setOption("ad_mode","forward")
    J.init()
    m=MX("m",3,1)
    [JT] = J.call([m])
    JT = MXFunction([m],[JT.T])
    JT.init()
    JT.input().set(n)
    JT.evaluate()
    H = Jacobian(JT,0,0)
    H.setOption("ad_mode","adjoint")
    H.init()
    H.input().set(n)
    H.evaluate()
    
    #print array(JT.output())
    #print array(H.output())
    
  def test_bugshape(self):
    self.message("shape bug")
    x=SX("x")
    y=SX("y")

    inp=SXMatrix(5,1)
    inp[0,0]=x
    inp[3,0]=y

    f=SXFunction([inp],[[x+y,x,y]])
    f.init()
    J=Jacobian(f,0,0)
    J.setOption("ad_mode","forward")
    J.init()
    J.input().set([2,7])
    J.evaluate()

    self.assertEqual(f.output().size1(),3,"Jacobian shape bug")
    self.assertEqual(f.output().size2(),1,"Jacobian shape bug")

    
  def test_bugglibc(self):
    self.message("Code that used to throw a glibc error")
    x=SX("x")
    y=SX("y")

    inp=SXMatrix(5,1)
    inp[0,0]=x
    inp[3,0]=y

    f=SXFunction([inp],[[x+y,x,y]])
    f.init()
    J=Jacobian(f,0,0)
    J.setOption("ad_mode","forward")
    J.init()
    J.input().set([2,7])
    J.evaluate()

    f=SXFunction([inp],[[x+y,x,y]])
    f.init()
    print f.input().shape
    J=Jacobian(f,0,0)
    
if __name__ == '__main__':
    unittest.main()

