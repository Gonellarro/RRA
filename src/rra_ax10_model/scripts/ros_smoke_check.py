import math,time
import rclpy
from rclpy.node import Node
from ackermann_msgs.msg import AckermannDriveStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from tf2_msgs.msg import TFMessage
class Check(Node):
 def __init__(self):
  super().__init__('ax10_isolated_check')
  self.odom=[]; self.joints=[]; self.tf=[]
  self.pub=self.create_publisher(AckermannDriveStamped,'/rra/model/cmd_ackermann',10)
  self.create_subscription(Odometry,'/rra/model/predicted_odom',lambda m:self.odom.append(m),10)
  self.create_subscription(JointState,'/rra/model/joint_states',lambda m:self.joints.append(m),10)
  self.create_subscription(TFMessage,'/tf',self.on_tf,10)
 def on_tf(self,m): self.tf += [t.child_frame_id for t in m.transforms]
rclpy.init(); n=Check(); start=time.monotonic()
while time.monotonic()-start<6:
 msg=AckermannDriveStamped(); msg.drive.speed=.2; msg.drive.steering_angle=.3; n.pub.publish(msg)
 rclpy.spin_once(n,timeout_sec=.05); time.sleep(.05)
end=time.monotonic()+1.3
while time.monotonic()<end: rclpy.spin_once(n,timeout_sec=.1)
assert n.odom and n.joints,'no hay odometria o articulaciones'
active=[x for x in n.odom if abs(x.twist.twist.linear.x-.2)<.001]
assert active,'ninguna salida en movimiento'
yaw=active[-1].twist.twist.angular.z; target=.2*math.tan(.3)/.320
assert abs(yaw-target)<.001,(yaw,target)
assert abs(n.odom[-1].twist.twist.linear.x)<1e-6,'timeout no detiene prediccion'
j=n.joints[-1]; assert abs(j.position[0]-.3)<.001 and abs(j.position[1]-.3)<.001
assert any(j.velocity[2] > 0 and abs(j.position[2]) > 0.01 for j in n.joints), 'ruedas no giran hacia delante'
assert 'front_left_steering_link' in n.tf and 'front_right_steering_link' in n.tf,('TF de direccion ausente',n.tf)
print('odom_count',len(n.odom),'joint_count',len(n.joints),'yaw_rate',yaw,'radius_m',.2/yaw,'timeout_speed',n.odom[-1].twist.twist.linear.x,'TF_steering_ok',True,flush=True)
n.destroy_node(); rclpy.shutdown()
