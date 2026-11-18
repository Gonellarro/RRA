#!/usr/bin/env python3
"""Pruebas de evitaciÃ³n SOLO en SITL, dentro de un namespace de red aislado."""
import hashlib, json, math, os, pathlib, signal, socket, subprocess, sys, tempfile, time
ROOT=pathlib.Path(__file__).resolve().parents[2]
BINARY=pathlib.Path.home()/'rra-sitl/ardurover'
DEPS=pathlib.Path.home()/'rra-sitl/deps-pymavlink-2.4.50'
EXPECTED='f453fd8217b9d798c873e5c424e139a2a3597b52e31658f76b2c177b523391af'
SIM_HOME='-35.363261,149.165230,584,0'

def inner(folder):
    original=os.environ['RRA_ORIGINAL_NETNS']
    if os.readlink('/proc/self/ns/net')==original: raise RuntimeError('No hay aislamiento')
    subprocess.run(['/usr/sbin/ip','link','set','lo','up'],check=True)
    links=json.loads(subprocess.check_output(['/usr/sbin/ip','-j','link']))
    if [x['ifname'] for x in links]!=['lo']: raise RuntimeError('Red no aislada')
    sys.path.insert(0,str(DEPS)); os.environ['MAVLINK20']='1'
    from pymavlink import mavutil
    defaults=pathlib.Path(folder)/'simulation-only.parm'
    profile='''\n# SOLO SITL: no cargar en la Matek\nRNGFND1_TYPE 10\nRNGFND1_MIN 0.2\nRNGFND1_MAX 2\nRNGFND1_ORIENT 0\nPRX1_TYPE 4\nAVOID_ENABLE 2\nAVOID_MARGIN 1\nAVOID_BACKUP_SPD 0\nOA_TYPE 0\nFS_GCS_ENABLE 0\nFS_THR_ENABLE 0\nRC_PROTOCOLS 0\nARMING_CHECK 0\nCRUISE_SPEED 1\nCRUISE_THROTTLE 30\n'''
    defaults.write_text((ROOT/'codex_handoff/sitl/rover-oficial-4.7.2.parm').read_text()+profile)
    f=open(pathlib.Path(folder)/'sitl.log','w')
    args=[str(BINARY),'--model','rover','--home='+SIM_HOME,'--defaults='+str(defaults),'--serial0=udpclient:127.0.0.1:14690','--serial2=udpclient:127.0.0.1:14692','--sim-address=127.0.0.1']
    p=subprocess.Popen(args,cwd=folder,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
    ev=open(pathlib.Path(folder)/'events.jsonl','w',encoding='utf8')
    def log(kind,**kw):
        data=dict(t=round(time.monotonic(),3),event=kind,**kw); print(json.dumps(data),flush=True); ev.write(json.dumps(data)+'\n'); ev.flush()
    state={'mode':None,'armed':False,'speed':None,'servo3':None,'last_sensor':None,'lat':None,'lon':None,'relative_alt':None}
    conn=None; last={}
    def receive():
        while True:
            m=conn.recv_match(blocking=False)
            if not m: break
            typ=m.get_type()
            if typ=='HEARTBEAT' and m.get_srcSystem()==1 and m.get_srcComponent()==1:
                state['mode']=int(m.custom_mode); state['armed']=bool(m.base_mode&128)
            elif typ=='VFR_HUD': state['speed']=float(m.groundspeed)
            elif typ=='SERVO_OUTPUT_RAW': state['servo3']=int(m.servo3_raw)
            elif typ=='DISTANCE_SENSOR' and m.get_srcSystem()==1 and m.get_srcComponent()==1:
                state['last_sensor']=int(m.current_distance)
            elif typ=='GLOBAL_POSITION_INT': state.update(lat=m.lat,lon=m.lon,relative_alt=m.relative_alt)
            elif typ=='STATUSTEXT': log('status',text=m.text)
            last[typ]=m
    def src(s,c): conn.mav.srcSystem=s; conn.mav.srcComponent=c
    def pump(seconds,distance=180,rc=False,guided=False,companion=True):
        begin=time.monotonic(); next_sensor=next_hb=next_cmd=0; samples=[]
        while time.monotonic()-begin<seconds:
            now=time.monotonic()
            if now>=next_hb:
                src(255,190); conn.mav.heartbeat_send(6,8,0,0,4); next_hb=now+1
                if companion:
                    src(1,191); conn.mav.heartbeat_send(18,8,0,0,4)
            if distance is not None and now>=next_sensor:
                src(1,192); conn.mav.distance_sensor_send(int(now*1000)&0xffffffff,20,200,int(distance),1,0,0,0)
                next_sensor=now+0.1
            if now>=next_cmd:
                if rc:
                    src(255,190); conn.mav.rc_channels_override_send(1,1,1500,65535,1600,65535,65535,65535,65535,65535)
                if guided and companion:
                    src(1,191); conn.mav.set_position_target_local_ned_send(int(now*1000)&0xffffffff,1,1,1,0x0de7,0,0,0,0.4,0,0,0,0,0,0,0)
                next_cmd=now+0.2
            receive(); samples.append((round(now-begin,2),state['speed'],state['servo3'],state['last_sensor']))
            time.sleep(.03)
        return samples
    def mode(n):
        src(255,190); conn.mav.set_mode_send(1,1,n)
        end=time.monotonic()+10
        while time.monotonic()<end:
            pump(.4)
            if state['mode']==n: log('mode',mode=n); return
        raise RuntimeError('No entro modo '+str(n))
    def stage(name,secs=8,**kw):
        log('stage_start',stage=name,options=kw)
        samples=pump(secs,**kw)
        log('stage_end',stage=name,mode=state['mode'],armed=state['armed'],samples=samples[::max(1,len(samples)//12)],end_speed=state['speed'],servo3=state['servo3'],sensor=state['last_sensor'])
    try:
        for _ in range(120):
            try: conn=mavutil.mavlink_connection('tcp:127.0.0.1:5762',source_system=255,source_component=190);break
            except OSError: time.sleep(.25)
        if conn is None: raise RuntimeError('SITL no disponible')
        log('start',binary_sha256=EXPECTED,netns=os.readlink('/proc/self/ns/net'))
        pump(10)
        src(255,190); conn.mav.request_data_stream_send(1,1,0,5,1)
        expected_params = {'RNGFND1_TYPE':10, 'RNGFND1_MIN':0.2, 'RNGFND1_MAX':2,
                           'PRX1_TYPE':4, 'AVOID_ENABLE':2, 'AVOID_MARGIN':1,
                           'AVOID_BACKUP_SPD':0, 'OA_TYPE':0, 'FS_GCS_ENABLE':0}
        for name, expected in expected_params.items():
            src(255,190); conn.mav.param_request_read_send(1,1,name.encode(),-1)
            end=time.monotonic()+4; value=None
            while time.monotonic()<end:
                pump(.12)
                m=last.get('PARAM_VALUE')
                if m and str(m.param_id)==name: value=m.param_value;break
            log('parameter',name=name,value=value)
            if value is None: raise RuntimeError('No se lee '+name)
            if abs(value - expected) > 0.001: raise RuntimeError('Valor inesperado de '+name)
        stage('warmup',35)
        src(255,190); conn.mav.command_long_send(1,1,400,0,1,0,0,0,0,0,0)
        pump(3)
        if not state['armed']: raise RuntimeError('No armado SITL')
        log('armed_sitl')
        if os.environ.get('RRA_TEST_CASE') == 'extra':
            mode(7)
            stage('SIMPLE_clear',8,rc=True,distance=180)
            stage('SIMPLE_obstacle',10,rc=True,distance=40)
            stage('SIMPLE_sensor_lost',8,rc=True,distance=None)
            try:
                mode(12)
            except RuntimeError as exc:
                log('mode_unavailable',mode='SMART_RTL',reason=str(exc))
            else:
                stage('SMART_RTL_clear',8,distance=180)
                stage('SMART_RTL_obstacle',10,distance=40)
                stage('SMART_RTL_sensor_lost',8,distance=None)
            mode(4)
        elif os.environ.get('RRA_TEST_CASE') == 'auto':
            # MisiÃ³n local ficticia, solicitada y confirmada mediante MAVLink.
            if state['lat'] is None or state['lon'] is None: raise RuntimeError('No hay posicion SITL')
            lat,lon=state['lat'],state['lon']
            src(255,190); conn.mav.mission_count_send(1,1,2,0)
            uploaded=set(); ack=None; deadline=time.monotonic()+25
            while time.monotonic()<deadline:
                pump(.1)
                for typ in ('MISSION_REQUEST_INT','MISSION_REQUEST'):
                    req=last.pop(typ,None)
                    if req:
                        seq=req.seq
                        if seq not in (0,1): raise RuntimeError('Secuencia invalida')
                        src(255,190)
                        conn.mav.mission_item_int_send(1,1,seq,6,16,int(seq==0),1,0,0,0,0,lat+(3000 if seq else 0),lon,0,0)
                        uploaded.add(seq);log('mission_item',seq=seq)
                msg=last.pop('MISSION_ACK',None)
                if msg: ack=msg.type;break
            if ack!=0 or uploaded!={0,1}: raise RuntimeError('Fallo al subir mision SITL: '+str((ack,uploaded)))
            log('mission_uploaded',count=2)
            mode(10)
            stage('AUTO_clear',10,distance=180)
            stage('AUTO_obstacle',10,distance=40)
            stage('AUTO_sensor_lost',8,distance=None)
            stage('AUTO_companion_lost',8,companion=False,distance=180)
            mode(11)
            stage('RTL_clear',8,distance=180)
            stage('RTL_obstacle',10,distance=40)
            stage('RTL_sensor_lost',8,distance=None)
            mode(5)
            stage('LOITER_obstacle',5,distance=40)
            mode(4)
        else:
            for name,mod in [('MANUAL',0),('STEERING',3),('ACRO',1)]:
                mode(4);pump(3);mode(mod)
                stage(name+'_clear',8,rc=True,distance=180)
                stage(name+'_obstacle',10,rc=True,distance=40)
                stage(name+'_sensor_lost',8,rc=True,distance=None)
            mode(4);pump(3);mode(15)
            stage('GUIDED_clear',8,guided=True,distance=180)
            stage('GUIDED_obstacle',10,guided=True,distance=40)
            stage('GUIDED_sensor_lost',8,guided=True,distance=None)
            stage('GUIDED_companion_lost',8,guided=False,companion=False,distance=180)
            mode(4);stage('HOLD_obstacle',5,distance=40)
        log('done',result='completed',note='simulacion terminada; revisar etapas y validez de sensores')
    finally:
        if conn: conn.close()
        if p.poll() is None:
            os.killpg(p.pid,signal.SIGTERM)
            try:p.wait(timeout=8)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
        log('sitl_exit',returncode=p.returncode); ev.close();f.close()

def main():
    if len(sys.argv)>1 and sys.argv[1]=='--inside': inner(sys.argv[2]);return
    if hashlib.sha256(BINARY.read_bytes()).hexdigest()!=EXPECTED: raise RuntimeError('Hash SITL incorrecto')
    out=ROOT/'codex_handoff/evidencias/evitacion-sitl-20261118';out.mkdir(parents=True,exist_ok=True)
    folder=tempfile.mkdtemp(prefix='prueba-',dir=out)
    env=dict(os.environ,RRA_ORIGINAL_NETNS=os.readlink('/proc/self/ns/net'),RRA_TEST_CASE=os.environ.get('RRA_TEST_CASE','modes'))
    result=subprocess.run(['unshare','-Urn',sys.executable,str(pathlib.Path(__file__).resolve()),'--inside',folder],env=env)
    print('EVIDENCIA',folder,'EXIT',result.returncode,flush=True)
    raise SystemExit(result.returncode)
if __name__=='__main__':main()
