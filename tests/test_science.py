import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pipeline import transform,score_distance
class Physics(unittest.TestCase):
 def test_unit_slope_normalization(self):
  a=transform(np.array([50.]),np.array([1000.]),np.array([30.]),np.array([2.]),np.array([.5]),np.array([1e-6]),31557600)
  self.assertAlmostEqual(10**a[0,0],.5)
  self.assertAlmostEqual(10**a[0,1],.05)
  self.assertAlmostEqual(10**a[0,2],.04)
 def test_thickness_covariance(self):
  a=transform(np.array([20.,40.]),np.array([1000.,1000.]),np.array([10.,10.]),np.array([2.,2.]),np.array([.5,.5]),np.array([1e-6,1e-6]),31557600)
  self.assertAlmostEqual(10**(a[1,1]-a[0,1]),2)
  self.assertAlmostEqual(10**(a[1,2]-a[0,2]),.5)
  self.assertAlmostEqual(10**(a[1,4]-a[0,4]),.5)
 def test_no_fabricated_arcadia_flow(self):
  a=transform(np.array([50.]),None,None,np.array([1.]),np.array([.9]),np.array([1e-6]),59355072)
  self.assertTrue(np.isnan(a[0,:2]).all());self.assertTrue(np.isfinite(a[0,2:]).all())
 def test_skin_depth_period(self):
  args=(np.array([50.]),None,None,np.array([2.]),np.array([.5]),np.array([1e-6]))
  a=transform(*args,100);b=transform(*args,400)
  self.assertAlmostEqual(10**(b[0,4]-a[0,4]),2)
 def test_identical_vector_score(self):
  x=np.array([1.,2.,3.]);d=score_distance(x,x,[1,1,1],[.2,.3,.5]);self.assertEqual(100*np.exp(-.5*d*d),100)
 def test_weighted_distance(self):
  d=score_distance(np.array([1.,0.]),np.array([0.,0.]),[2.,1.],[.8,.2]);self.assertAlmostEqual(d,np.sqrt(.2))
if __name__=='__main__':unittest.main()
