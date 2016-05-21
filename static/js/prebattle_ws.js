try{
    var sock = new WebSocket('ws://' + window.location.host + '/prebattle/ws');
}
catch(err){
    var sock = new WebSocket('wss://' + window.location.host + '/prebattle/ws');
}

// show message in div#subscribe
function showMessage(message) {
    var messageElem = $('.centered_table');
    messageElem.html(message);
}

function sendMessage(){
    var msg = $('#message');
    sock.send(msg.val());
    msg.val('').focus();
}

sock.onopen = function(){
    showMessage('Connection to server started')
}

// send message from form
// $('#submit').click(function() {
//     sendMessage();
// });
//
// $('#message').keyup(function(e){
//     if(e.keyCode == 13){
//         sendMessage();
//     }
// });

// income message handler
sock.onmessage = function(event) {
  var data = JSON.parse(event.data)
  if (data.message) {
    showMessage(data.message);
  }
  if (data.redirect){
    window.location.href = data.redirect;
  }
};

$('#signout').click(function(){
    window.location.href = "signout"
});

sock.onclose = function(event){
    if(event.wasClean){
        showMessage('Clean connection end')
    }else{
        showMessage('Connection broken')
    }
};

sock.onerror = function(error){
    showMessage(error);
}
