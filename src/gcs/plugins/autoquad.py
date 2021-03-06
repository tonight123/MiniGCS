from PyQt5.QtCore import Qt  # , pyqtSignal
from PyQt5.QtWidgets import QGridLayout, QLabel, QPushButton, QMessageBox
from pymavlink.mavutil import mavlink
from plugins.common import AbstractControlPanel

MAV_CMD_ACKS = {
    mavlink.MAV_CMD_ACK_OK : 'Command executed',
    mavlink.MAV_CMD_ACK_ERR_FAIL : 'Generic error',
    mavlink.MAV_CMD_ACK_ERR_ACCESS_DENIED : 'Command refused',
    mavlink.MAV_CMD_ACK_ERR_NOT_SUPPORTED : 'Command not supported',
    mavlink.MAV_CMD_ACK_ERR_COORDINATE_FRAME_NOT_SUPPORTED : 'Coordinate frame not supported',
    mavlink.MAV_CMD_ACK_ERR_COORDINATES_OUT_OF_RANGE : 'Invalid coordinate values',
    mavlink.MAV_CMD_ACK_ERR_X_LAT_OUT_OF_RANGE : 'Invalid latitude value',
    mavlink.MAV_CMD_ACK_ERR_Y_LON_OUT_OF_RANGE : 'Invalid longitude value',
    mavlink.MAV_CMD_ACK_ERR_Z_ALT_OUT_OF_RANGE : 'Invalid altitude value'
}

class AutoQuadControlPanel(AbstractControlPanel):

    __mavlinkMessageTypes = ['AQ_TELEMETRY_F', 'AQ_ESC_TELEMETRY']
    cmdSent = 0
    syncParamsFromUAV = False

    def __init__(self, parent = None):
        super().__init__(parent)
        l = QGridLayout()
        row = 0
        l.addWidget(QLabel('AutoQuad Tools'), row, 0, 1, 3, Qt.AlignLeft)
        row += 1
        self.fromSDButton = QPushButton('From SD')
        self.toSDButton = QPushButton('To SD')
        self.readFromFlashButton = QPushButton('Reload Flash')
        self.saveToFlashButton = QPushButton('Save Flash')
        self.dIMUTareButton = QPushButton('DIMU Tare')
        self.magCalibButton = QPushButton('MAG Calib.')
        self.calibSaveButton = QPushButton('Calib. Save')
        self.calibReadButton = QPushButton('Calib. Read')
        self.fromSDButton.clicked.connect(lambda: \
            self.__sendMAVLinkLongMessage(command=mavlink.MAV_CMD_PREFLIGHT_STORAGE,
                                          param1=3,
                                          syncParams=True))
        self.toSDButton.clicked.connect(lambda: \
            self.__sendMAVLinkLongMessage(command=mavlink.MAV_CMD_PREFLIGHT_STORAGE,
                                          param1=2))
        self.readFromFlashButton.clicked.connect(lambda: \
            self.__sendMAVLinkLongMessage(command=mavlink.MAV_CMD_PREFLIGHT_STORAGE,
                                          param1=0,
                                          syncParams=True))
        self.saveToFlashButton.clicked.connect(lambda: \
            self.__sendMAVLinkLongMessage(command=mavlink.MAV_CMD_PREFLIGHT_STORAGE,
                                          param1=1))
        self.calibSaveButton.clicked.connect(lambda: \
            self.__sendMAVLinkLongMessage(target_component=mavlink.MAV_COMP_ID_IMU,
                                          command=mavlink.MAV_CMD_PREFLIGHT_STORAGE,
                                          param1=1))
        self.calibReadButton.clicked.connect(lambda: \
            self.__sendMAVLinkLongMessage(target_component=mavlink.MAV_COMP_ID_IMU,
                                          command=mavlink.MAV_CMD_PREFLIGHT_STORAGE,
                                          param1=0,
                                          syncParams=True))
        self.dIMUTareButton.clicked.connect(lambda: \
            self.__sendMAVLinkLongMessage(command=mavlink.MAV_CMD_PREFLIGHT_CALIBRATION,
                                          param5=1))
        self.magCalibButton.clicked.connect(lambda: \
            self.__sendMAVLinkLongMessage(command=mavlink.MAV_CMD_PREFLIGHT_CALIBRATION,
                                          param2=1))
        l.addWidget(self.fromSDButton, row, 0, 1, 1, Qt.AlignLeft)
        l.addWidget(self.toSDButton, row, 2, 1, 1, Qt.AlignLeft)
        row += 1
        l.addWidget(self.readFromFlashButton, row, 0, 1, 1, Qt.AlignLeft)
        l.addWidget(self.saveToFlashButton, row, 2, 1, 1, Qt.AlignLeft)
        row += 1
        l.addWidget(self.dIMUTareButton, row, 0, 1, 1, Qt.AlignLeft)
        l.addWidget(self.magCalibButton, row, 2, 1, 1, Qt.AlignLeft)
        row += 1
        l.addWidget(self.calibSaveButton, row, 0, 1, 1, Qt.AlignLeft)
        l.addWidget(self.calibReadButton, row, 2, 1, 1, Qt.AlignLeft)
        row += 1
        l.setRowStretch(row, 1)
        self.setLayout(l)

    def __sendMAVLinkLongMessage(self, target_system = 255, # set target system to 255 to let telemetry.py auto correct the values
                                       target_component = 0,
                                       command = 0,
                                       confirmation = 0,
                                       param1 = 0,
                                       param2 = 0,
                                       param3 = 0,
                                       param4 = 0,
                                       param5 = 0,
                                       param6 = 0,
                                       param7 = 0,
                                       syncParams = False):
        msg = mavlink.MAVLink_command_long_message(target_system, target_component,
                                                   command, confirmation,
                                                   param1, param2, param3,
                                                   param4, param5, param6, param7)
        self.__addMessageType('COMMAND_ACK')
        self.cmdSent = command
        self.syncParamsFromUAV = syncParams
        self.mavlinkTxSignal.emit(msg)

    def tabName(self):
        return 'AutoQuad'

    def __addMessageType(self, msgType):
        if msgType not in self.__mavlinkMessageTypes:
            self.__mavlinkMessageTypes.append(msgType)

    def __removeMessageType(self, msgType):
        if msgType in self.__mavlinkMessageTypes:
            self.__mavlinkMessageTypes.remove(msgType)

    def registerMavlinkMessageListeners(self):
        return self.__mavlinkMessageTypes

    def mavlinkMessageReceived(self, msg):
        if msg.get_type() == 'COMMAND_ACK' and msg.command == self.cmdSent:
            if msg.result in MAV_CMD_ACKS:
                if msg.result == mavlink.MAV_CMD_ACK_OK:
                    if self.syncParamsFromUAV:
                        self.syncParamsFromUAV = False
                        self.uas.fetchAllOnboardParameters()
                    QMessageBox.information(self, 'Information', MAV_CMD_ACKS[msg.result], QMessageBox.Ok)
                else:
                    QMessageBox.critical(self, 'Error', MAV_CMD_ACKS[msg.result], QMessageBox.Ok)
            self.__removeMessageType('COMMAND_ACK')
