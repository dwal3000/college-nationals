function getXMLHTTP(){
  var A = null;
  
  try{
    A = new ActiveXObject("Msxml2.XMLHTTP");
  }catch(e){
    try{
      A = new ActiveXObject("Microsoft.XMLHTTP");
    } catch(oc){
      A = null;
    }
  }
  
  if(!A && typeof XMLHttpRequest != "undefined") {
    A = new XMLHttpRequest();
  }
  
  return A;
}
