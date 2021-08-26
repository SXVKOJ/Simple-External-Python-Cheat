import pymem
import pymem.process
import time
import math
import threading
import keyboard
from offsets import *


pm = pymem.Pymem("csgo.exe")

client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll

engine = pymem.process.module_from_name(pm.process_handle, "engine.dll").lpBaseOfDll


def normalizeAngles(x, y):
    if x > 89:
        x -= 360
    if x < -89:
        x += 360
    if y > 180:
        y -= 360
    if y < -180:
        y += 180

    return x, y


def calcAngle(l_x, l_y, l_z, e_x, e_y, e_z):
    d_x = l_x - e_x
    d_y = l_y - e_y
    d_z = l_z - e_z

    hyp = math.sqrt(d_x * d_x + d_y * d_y + d_z * d_z)

    x = math.atan(d_z / hyp) * 180 / math.pi
    y = math.atan(d_y / d_x) * 180 / math.pi

    if d_x > 0:
        y += 180

    return x, y


def bhop():
    while not keyboard.is_pressed("end"):
        if pm.read_int(client + dwLocalPlayer):
            local_player = pm.read_int(client + dwLocalPlayer)
            flags = pm.read_int(local_player + m_fFlags)

            if keyboard.is_pressed(" ") and flags == 257:
                velocity = pm.read_int(local_player + m_vecVelocity)

                if velocity != 0:
                    pm.write_int(client + dwForceJump, 5)
                    time.sleep(0.15)
                    pm.write_int(client + dwForceJump, 4)
        else:
            print("LocalPlayer is not found!")


def AimThread():
    while not keyboard.is_pressed("end"):
        if pm.read_int(client + dwLocalPlayer):
            local_player = pm.read_int(client + dwLocalPlayer)
            client_state = pm.read_int(engine + dwClientState)

            for i in range(64):
                if pm.read_int(client + dwEntityList + i * 0x10):
                    entity = pm.read_int(client + dwEntityList + i * 0x10)
                    entity_hp = pm.read_int(entity + m_iHealth)

                    if entity_hp > 0 and keyboard.is_pressed("alt"):
                        local_player_id = pm.read_int(client_state + dwClientState_GetLocalPlayer)
                        spotted_by_mask = pm.read_int(entity + m_bSpottedByMask)

                        bone_matrix = pm.read_int(entity + m_dwBoneMatrix)

                        entity_x = pm.read_float(bone_matrix + 0x30 * 8 + 0xC)
                        entity_y = pm.read_float(bone_matrix + 0x30 * 8 + 0x1C)
                        entity_z = pm.read_float(bone_matrix + 0x30 * 8 + 0x2C)

                        local_x = pm.read_float(local_player + m_vecOrigin)
                        local_y = pm.read_float(local_player + m_vecOrigin + 0x4)
                        local_z = pm.read_float(local_player + m_vecOrigin + 0x8) + \
                                    pm.read_float(local_player + m_vecViewOffset + 0x8)

                        view_angle_x = pm.read_float(client_state + dwClientState_ViewAngles)
                        view_angle_y = pm.read_float(client_state + dwClientState_ViewAngles + 0x4)

                        x, y = calcAngle(local_x,
                                         local_y,
                                         local_z,

                                         entity_x,
                                         entity_y,
                                         entity_z)

                        diff_x = x - view_angle_x
                        diff_y = y - view_angle_y

                        diff_x, diff_y = normalizeAngles(diff_x, diff_y)

                        if spotted_by_mask & (1 << local_player_id):
                            pm.write_float(client_state + dwClientState_ViewAngles, view_angle_x + diff_x)
                            pm.write_float(client_state + dwClientState_ViewAngles + 0x4, view_angle_y + diff_y)

                            crosshair_id = pm.read_int(local_player + m_iCrosshairId)

                            if crosshair_id != 0 and crosshair_id < 64:
                                t_entity = pm.read_int(client + dwEntityList + (crosshair_id - 1) * 0x10)

                                if pm.read_int(t_entity + m_iTeamNum) != pm.read_int(local_player + m_iTeamNum):
                                    pm.write_int(client + dwForceAttack, 5)
                                    time.sleep(0.15)
                                    pm.write_int(client + dwForceAttack, 4)


def glow_esp():
    while not keyboard.is_pressed("end"):
        if pm.read_int(client + dwLocalPlayer):
            local_player = pm.read_int(client + dwLocalPlayer)

            for i in range(64):
                if pm.read_int(client + dwEntityList + i * 0x10):
                    entity = pm.read_int(client + dwEntityList + i * 0x10)

                    entity_team = pm.read_int(entity + m_iTeamNum)
                    local_player_team = pm.read_int(local_player + m_iTeamNum)

                    glow_manager = pm.read_int(client + dwGlowObjectManager)
                    glow_index = pm.read_int(entity + m_iGlowIndex)

                    if entity_team == local_player_team:
                        pm.write_float(glow_manager + (glow_index * 0x38) + 0x8, float(0))
                        pm.write_float(glow_manager + (glow_index * 0x38) + 0xC, float(1))
                        pm.write_float(glow_manager + (glow_index * 0x38) + 0x10, float(0))
                        pm.write_float(glow_manager + (glow_index * 0x38) + 0x14, float(1))
                    else:
                        pm.write_float(glow_manager + (glow_index * 0x38) + 0x8, float(1))
                        pm.write_float(glow_manager + (glow_index * 0x38) + 0xC, float(0))
                        pm.write_float(glow_manager + (glow_index * 0x38) + 0x10, float(1))
                        pm.write_float(glow_manager + (glow_index * 0x38) + 0x14, float(1))

                    pm.write_int(glow_manager + (glow_index * 0x38) + 0x28, 1)
                    pm.write_int(glow_manager + (glow_index * 0x38) + 0x29, 1)


def recoil_control_system():

    o_punch_x = 0.0
    o_punch_y = 0.0

    while not keyboard.is_pressed("end"):
        if pm.read_int(client + dwLocalPlayer):
            local_player = pm.read_int(client + dwLocalPlayer)

            client_state = pm.read_int(engine + dwClientState)

            punch_x = pm.read_float(local_player + m_viewPunchAngle)

            punch_y = pm.read_float(local_player + m_viewPunchAngle + 0x4)

            view_angle_x = pm.read_float(client_state + dwClientState_ViewAngles)
            view_angle_y = pm.read_float(client_state + dwClientState_ViewAngles + 0x4)

            if pm.read_int(local_player + m_iShotsFired) > 1:
                new_x = view_angle_x + o_punch_x - punch_x
                new_y = view_angle_y + o_punch_y - punch_y

                pm.write_float(client_state + dwClientState_ViewAngles, float(new_x))
                pm.write_float(client_state + dwClientState_ViewAngles + 0x4, float(new_y))

            o_punch_x = punch_x
            o_punch_y = punch_y



def main():
    BHOP = threading.Thread(target=bhop)
    BHOP.start()

    AIM = threading.Thread(target=AimThread)
    AIM.start()

    WH = threading.Thread(target=glow_esp)
    WH.start()

    RCS = threading.Thread(target=recoil_control_system)
    RCS.start()


if __name__ == "__main__":
    main()
