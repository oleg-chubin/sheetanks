try{
    var sock = new WebSocket('ws://' + window.location.host + '/arena/ws');
}
catch(err){
    var sock = new WebSocket('wss://' + window.location.host + '/arena/ws');
}

// show message in div#subscribe
function showMessage(message) {
    var messageElem = $('#subscribe'),
        height = 0,
        date = new Date();
        options = {hour12: false};
    messageElem.append($('<p>').html('[' + date.toLocaleTimeString('en-US', options) + '] ' + message + '\n'));
    messageElem.find('p').each(function(i, value){
        height += parseInt($(this).height());
    });

    messageElem.animate({scrollTop: height});
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
$('#submit').click(function() {
    sendMessage();
});

$('#message').keyup(function(e){
    if(e.keyCode == 13){
        sendMessage();
    }
});


function update_ally(parsed_data)
{
    var account_id = parsed_data.account_id;
    $('.teammate').not("#myVehicle").remove();
    for (key in parsed_data.vehicles) {
        if (parsed_data.vehicles.hasOwnProperty(key)){
            if (key != account_id){
                tank = $('<img src="/static/images/tank.png" class="teammate">');
                $('.arena_field').append(tank);
                var pos = parsed_data.vehicles[key];
                tank.css({top: pos.y - 50, left: pos.x - 50, position:'absolute'});
            }
        }
    }
}

function sync_arena(parsed_data){
    for (key in parsed_data.ally) {
        if (parsed_data.ally.hasOwnProperty(key)){
            tank = $('<img src="/static/images/tank.png" class="teammate">');
            $('.arena_field').append(tank);
            var pos = parsed_data.ally[key];
            tank.css({top: pos.y - 50, left: pos.x - 50, position:'absolute'});
        }
    }
    for (key in parsed_data.enemy) {
        if (parsed_data.enemy.hasOwnProperty(key)){
            tank = $('<img src="/static/images/tank.png" class="enemy mirrored">');
            $('.arena_field').append(tank);
            var pos = parsed_data.enemy[key];
            tank.css(
                {
                    top: pos.y - 50,
                    right: pos.x - 50,
                    position:'absolute',
                });
        }
    }
}

// income message handler
sock.onmessage = function(event) {
  var parsed_data = JSON.parse(event.data);
  if (parsed_data.command == 'update_vehicles'){
    update_ally(parsed_data);
  }
  if (parsed_data.command == 'sync_arena'){
    sync_arena(parsed_data);
  }
//   showMessage(event.data);
};

$(function(){
    $('.arena_field').click(function(event){
        sock.send(
            JSON.stringify(
                {
                    "y": event.offsetY,
                    "x": event.offsetX,
                    "height": $(this).height(),
                    "width": $(this).width()
                }
            )
        );
        var tank;
        tank = $('#myVehicle');
        if (!tank.length) {
            tank = $('<img src="/static/images/tank.png" id="myVehicle">');
            $(this).append(tank);
        }
        tank.css({top: event.offsetY - 50, left: event.offsetX - 50, position:'absolute'});
    });
})

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
