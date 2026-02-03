// const { app, BrowserWindow } = require("electron");
// const { spawn } = require("child_process");
// const path = require("path");
//
// let flaskProcess;
//
// function createWindow() {
//   const win = new BrowserWindow({
//     width: 1200,
//     height: 800,
//     webPreferences: {
//       nodeIntegration: false,
//       contextIsolation: true
//     }
//   });
//
//   win.loadURL("http://127.0.0.1:9001");
// }
//
// app.whenReady().then(() => {
//   flaskProcess = spawn("python", ["server.py"], {
//     cwd: path.join(__dirname, "../backend"),
//     detached: true,
//     stdio: "ignore"
//   });
//
//   setTimeout(createWindow, 2000);
// });
//
// app.on("window-all-closed", () => {
//   if (process.platform !== "darwin") {
//     app.quit();
//   }
// });
//
// app.on("will-quit", () => {
//   if (flaskProcess) flaskProcess.kill();
// });












// const { app, BrowserWindow } = require("electron");
// const { spawn } = require("child_process");
// const path = require("path");
// const http = require("http");
//
// let pyProcess=null;
//
// function startPythonServer(){
//   const serverPath="C:\\Users\\shivs\\PyCharmMiscProject\\client-dashboard-app\\python\\server.exe";
//   pyProcess=spawn(serverPath,["--electron"],{cwd:path.dirname(serverPath),stdio:"inherit"});
// }
//
// function createWindow(){
//   const win=new BrowserWindow({width:1200,height:800});
//   win.loadURL("http://192.168.1.6:9001");
// }
//
// app.whenReady().then(()=>{
//   startPythonServer();
//   setTimeout(createWindow,3000);
// });
//
// app.on("window-all-closed",()=>{
//   const req=http.request({hostname:"192.168.1.6",port:9001,path:"/shutdown",method:"POST"});
//   req.on("error",()=>{});
//   req.end();
//   if(pyProcess)pyProcess.kill();
//   app.quit();
// });














//
//const { app, BrowserWindow } = require("electron");
//const { spawn } = require("child_process");
//const path = require("path");
//const http = require("http");
//
//let pyProcess=null;
//
//function startPythonServer(){
//  const serverPath="C:\\Users\\shivs\\PyCharmMiscProject\\client-dashboard-app\\python\\server.exe";
//  pyProcess=spawn(serverPath,["--electron"],{cwd:path.dirname(serverPath),stdio:"inherit"});
//}
//
//function createWindow(){
//  const win=new BrowserWindow({width:1200,height:800});
//  win.loadURL("http://10.0.5.28:9001");
//}
//
//app.whenReady().then(()=>{
//  startPythonServer();
//  setTimeout(createWindow,3000);
//});
//
//app.on("window-all-closed",()=>{
//  const req=http.request({hostname:"10.0.5.28",port:9001,path:"/shutdown",method:"POST"});
//  req.on("error",()=>{});
//  req.end();
//  if(pyProcess)pyProcess.kill();
//  app.quit();
//});
















const { app, BrowserWindow } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const http = require("http");

let pyProcess=null;

function startPythonServer(){
  const serverPath="C:\\Users\\shivs\\PyCharmMiscProject\\client-dashboard-app\\python\\server.exe";
  pyProcess=spawn(serverPath,["--electron"],{cwd:path.dirname(serverPath),stdio:"inherit"});
}

function createWindow(){
  const win=new BrowserWindow({width:1200,height:800});
  win.loadURL("http://182.79.87.158:9001");
}

app.whenReady().then(()=>{
  startPythonServer();
  setTimeout(createWindow,3000);
});

app.on("window-all-closed",()=>{
  const req=http.request({hostname:"182.79.87.158",port:9001,path:"/shutdown",method:"POST"});
  req.on("error",()=>{});
  req.end();
  if(pyProcess)pyProcess.kill();
  app.quit();
});
