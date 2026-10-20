
(function(){
"use strict";
var loginTab=document.getElementById("login-tab");
var signupTab=document.getElementById("signup-tab");
var loginForm=document.getElementById("login-form");
var signupForm=document.getElementById("signup-form");
var authPanel=document.getElementById("auth-panel");
var accountPanel=document.getElementById("account-panel");
var authFeedback=document.getElementById("auth-feedback");
var profileFeedback=document.getElementById("profile-feedback");
var formTitle=document.getElementById("form-title");
var formSubtitle=document.getElementById("form-subtitle");
var busy=false;

function message(target,text){target.textContent=text;target.classList.add("visible");}
function clearMessage(target){target.textContent="";target.classList.remove("visible");}
function cookie(name){
 var prefix=name+"=";
 var part=document.cookie.split("; ").find(function(item){return item.indexOf(prefix)===0;});
 return part?decodeURIComponent(part.slice(prefix.length)):"";
}
async function api(path,options){
 options=options||{};
 var headers=options.headers||{};
 if(options.body && !headers["Content-Type"]) headers["Content-Type"]="application/json";
 if(options.method && options.method!=="GET" && options.method!=="POST" && options.method!=="HEAD"){
  headers["X-CSRF-Token"]=cookie("genopedia_csrf");
 }
 if(options.method==="POST" && path==="/api/auth/logout") headers["X-CSRF-Token"]=cookie("genopedia_csrf");
 var response=await fetch(path,{method:options.method||"GET",headers:headers,body:options.body,credentials:"same-origin"});
 var body=null;
 if(response.status!==204){try{body=await response.json();}catch(_error){body=null;}}
 if(!response.ok){
  var errorText=(body && body.detail) ? body.detail : "The request could not be completed. Please try again.";
  if(Array.isArray(errorText)) errorText=errorText.map(function(item){return item.msg||"Invalid input";}).join(". ");
  throw new Error(errorText);
 }
 return body;
}
function setBusy(form,value,label){
 Array.from(form.querySelectorAll("button[type=submit]")).forEach(function(button){
  button.disabled=value;
  if(value){button.dataset.originalText=button.textContent;button.textContent=label||"Please wait…";}
  else if(button.dataset.originalText){button.textContent=button.dataset.originalText;delete button.dataset.originalText;}
 });
}
function showMode(mode){
 var signup=mode==="signup";
 loginTab.setAttribute("aria-selected",String(!signup));
 signupTab.setAttribute("aria-selected",String(signup));
 loginForm.hidden=signup;signupForm.hidden=!signup;
 formTitle.textContent=signup?"Create your account":"Welcome back";
 formSubtitle.textContent=signup?"Start with a private account for your Genopedia workspace.":"Sign in to access your Genopedia account and profile.";
 clearMessage(authFeedback);
}
loginTab.addEventListener("click",function(){showMode("login");});
signupTab.addEventListener("click",function(){showMode("signup");});
document.querySelectorAll("[data-toggle-password]").forEach(function(button){
 button.addEventListener("click",function(){
  var input=document.getElementById(button.dataset.togglePassword);
  var showing=input.type==="text";
  input.type=showing?"password":"text";
  button.textContent=showing?"Show":"Hide";
  button.setAttribute("aria-label",showing?"Show password":"Hide password");
 });
});
function renderAccount(user){
 authPanel.hidden=true;accountPanel.classList.add("visible");
 document.getElementById("account-title").textContent=user.display_name;
 document.getElementById("account-email").textContent=user.email;
 document.getElementById("profile-name").value=user.display_name;
 document.getElementById("avatar-initials").textContent=(user.display_name.trim().split(/s+/).slice(0,2).map(function(part){return part.charAt(0).toUpperCase();}).join("")||"G");
 var created=new Date(user.created_at);
 document.getElementById("profile-created").textContent="Account created "+(isNaN(created.getTime())?"recently":created.toLocaleDateString(undefined,{year:"numeric",month:"short",day:"numeric"}))+".";
}
function renderAuth(){
 accountPanel.classList.remove("visible");authPanel.hidden=false;showMode("login");
}
async function authSubmit(event,mode){
 event.preventDefault();if(busy)return;busy=true;
 var form=event.currentTarget;clearMessage(authFeedback);setBusy(form,true,mode==="signup"?"Creating account…":"Signing in…");
 var payload=Object.fromEntries(new FormData(form).entries());
 try{
  var user=await api(mode==="signup"?"/api/auth/signup":"/api/auth/login",{method:"POST",body:JSON.stringify(payload)});
  renderAccount(user);
 }catch(error){message(authFeedback,error.message||"Unable to sign in. Please check your details.");}
 finally{busy=false;setBusy(form,false);}
}
loginForm.addEventListener("submit",function(event){authSubmit(event,"login");});
signupForm.addEventListener("submit",function(event){authSubmit(event,"signup");});
document.getElementById("profile-form").addEventListener("submit",async function(event){
 event.preventDefault();if(busy)return;busy=true;clearMessage(profileFeedback);
 var form=event.currentTarget;setBusy(form,true,"Saving…");
 try{var user=await api("/api/users/me",{method:"PATCH",body:JSON.stringify({display_name:document.getElementById("profile-name").value})});renderAccount(user);message(profileFeedback,"Your profile has been updated.");}
 catch(error){message(profileFeedback,error.message||"Unable to save profile.");}
 finally{busy=false;setBusy(form,false);}
});
document.getElementById("logout-button").addEventListener("click",async function(){
 if(busy)return;busy=true;this.disabled=true;
 try{await api("/api/auth/logout",{method:"POST"});renderAuth();message(authFeedback,"You have signed out.");}
 catch(error){message(profileFeedback,error.message||"Unable to sign out.");}
 finally{busy=false;this.disabled=false;}
});
api("/api/auth/me").then(renderAccount).catch(function(){renderAuth();});
})();
