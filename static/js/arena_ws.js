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

function normalize_coords(coords){
    var div = $('.arena_field');
    var h = div.height();
    var w = div.width();
    return {
        'x': coords.x * w / 1000,
        'y': coords.y * h / 1000
    }
}

function update_ally(parsed_data)
{
    var account_id = parsed_data.account_id;
    $('.teammate').not("#myVehicle").remove();
    for (key in parsed_data.vehicles) {
        if (parsed_data.vehicles.hasOwnProperty(key)){
            var vehicle_info = parsed_data.vehicles[key];
            var tank = $('<img src="/static/images/' + vehicle_info.image +'" class="teammate">');
            $('.arena_field').append(tank);
            var pos = normalize_coords(vehicle_info);
            if (key != account_id){
                tank.css(
                    {
                        top: pos.y - vehicle_info.height/2,
                        left: pos.x - vehicle_info.width/2,
                        position:'absolute',
                        opacity: 0.4,
                        filter: "alpha(opacity=40)" /* For IE8 and earlier */
                    });
            }
            else{
                tank.css(
                    {
                        top: pos.y - vehicle_info.height/2,
                        left: pos.x - vehicle_info.width/2,
                        position:'absolute'
                    });
            }
        }
    }
}

function createBaseLine(div, x1,y1, x2,y2){
    var length = Math.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2));
  var angle  = Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI;
  var transform = 'rotate('+angle+'deg)';

    var line = $('<div>')
        .appendTo(div)
        .addClass('line')
        .css({
          'position': 'absolute',
          'transform': transform
        })
        .width(length)
        .offset({left: x1, top: y1});

    return line;
}

function createLine(div, offset) {
    var h = div.height();
    var w = div.width();
    return createBaseLine(div, w/2 + offset, 0, w/2 - offset, h);
}

function sync_arena(parsed_data){
    $('img.teammate,img.enemy').remove();
    $('div.line').remove();
    for (key in parsed_data.ally) {
        if (parsed_data.ally.hasOwnProperty(key)){
            var vehicle_info = parsed_data.ally[key];
            tank = $('<img src="/static/images/' + vehicle_info.image + '" class="teammate hint--bottom  hint--always">');
            $('.arena_field').append(tank);
            var pos = normalize_coords(parsed_data.ally[key]);
            tank.css(
                {
                    top: pos.y - vehicle_info.height/2,
                    left: pos.x - vehicle_info.width/2,
                    position:'absolute'
                });
        }
    }
    for (key in parsed_data.enemy) {
        if (parsed_data.enemy.hasOwnProperty(key)){
            var vehicle_info = parsed_data.enemy[key];
            tank = $('<img src="/static/images/' + vehicle_info.image + '" class="enemy mirrored">');
            $('.arena_field').append(tank);
            var pos = normalize_coords(parsed_data.enemy[key]);
            tank.data('hp', vehicle_info.hp + "/" + vehicle_info.initial_hp);
            tank.css(
                {
                    top: pos.y - vehicle_info.height/2,
                    right: pos.x - vehicle_info.width/2,
                    position:'absolute',
                });
        }
    }

    $.map(parsed_data.shots.enemy, function(data){
        shot = $('<img src="/static/images/burnout.png" class="burnout">');
        $('.arena_field').append(shot);
        var pos = normalize_coords(data);
        shot.css({top: pos.y - 25, left: pos.x - 25, position:'absolute'});
    })

    $.map(parsed_data.shots.ally, function(data){
        shot = $('<img src="/static/images/burnout.png" class="burnout">');
        $('.arena_field').append(shot);
        var pos = normalize_coords(data);
        shot.css({top: pos.y - 25, right: pos.x - 25, position:'absolute'});
    })

    createLine($('.arena_field'), parsed_data.divider);
}

function update_countdown(parsed_data){
    var countdown_div =$('.arena_field').find('.countdown');
    if (!countdown_div.length){
        var countdown_div = $('<div class="countdown"></div>');
        countdown_div.css({'text-align': 'center'});
        $('.arena_field').prepend(countdown_div);
    }
    countdown_div.html(parsed_data.left);
}

function update_shot(parsed_data){
    var shot_img =$('.arena_field').find('.shot');
    if (!shot_img.length){
        shot_img = $('<img src="/static/images/aim.png" class="shot">');
        $('.arena_field').prepend(shot_img);
    }
    var data = normalize_coords(parsed_data.data);
    shot_img.css(
        {
            top: data.y - 25,
            left: data.x - 25,
            position:'absolute',
        });
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
  if (parsed_data.command == 'update_countdown'){
    update_countdown(parsed_data);
  }
  if (parsed_data.command == 'update_shot'){
    update_shot(parsed_data);
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
