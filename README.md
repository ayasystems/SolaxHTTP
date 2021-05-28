# SolaxHTTP
SolaxHTTP domoticz plugin para su integración en domoticz


[Información](#informaci%C3%B3n)

[Instalación](#instalaci%C3%B3n)

[Actualización](#actualizaci%C3%B3n-del-plugin)

[Firmware modificado](#firmware-modificado)


## Información
![Solax inverter](https://github.com/ayasystems/SolaxHTTP/raw/master/solax.jpg)

![Domoticz_Solax_Plugin](https://github.com/ayasystems/SolaxHTTP/raw/master/domoticz_solax.jpg)

Más info -> https://domotuto.com/integracion-del-inversor-solar-solax-boost-en-domoticz/

## Instalación

1. Clona el repositorio dentro de tu carpeta de plugins de domoticz
```
cd domoticz/plugins
git clone https://github.com/ayasystems/SolaxHTTP.git
```
2. Reinicia domotiz
```
sudo systemctl stop domoticz
sudo systemctl start domoticz
```
3. Ve a la página de "Hardware" y añade un nuevo hardware, en tipo selecciona "Solax HTTP"
4. Especifica la ip de tu inversor solax
5. Recuerda permitir añadir nuevos dispositivos en el menú de ajustes


## Actualización del plugin


1. Para domoticz 
```
sudo systemctl stop domoticz
```
2. Ve al directorio del plugin y haz un git pull para que actualice la versión 
```
cd domoticz/plugins/SolaxHTTP
git pull
```
3. Start domoticz
```
sudo systemctl start domoticz
```
 
## Firmware modificado

Hay una versión de firmware modificado que permite conexión directa al pocket wifi, más información aquí -> https://blog.chrisoft.io/2021/02/14/firmwares-modificados-para-solax-pocket-wifi-v2/



