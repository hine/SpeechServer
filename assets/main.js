(function() {

  var hostname = location.host;
  var ws = new WebSocket("ws://" + hostname + "/ws");

  ws.onopen = function() {
    // WebSocketオープン時の挙動を書く
    ws.send(JSON.stringify({command: "voice_list"}));
  };

  ws.onmessage = function (evt) {
    // WebSocketでメッセージを受け取った時の処理をまとめて
    try {
      var messageData = JSON.parse(evt.data);
      parseMessage(messageData);
    } catch(e) {
      alert('受け取ったメッセージの形式が不正です [response]:' + messageData['response']);
    }
  };

  $('#speech-text').on('keydown', function(event) {
    if (event.keyCode == 13) {
      ws.send(JSON.stringify({command: "say", data: {text: $('#speech-text').val(), voice: $('#voice').val()}}));
      if (document.getElementById('enter_key_flag').checked) {
        $('#speech-text').val('');
      }
    }
  });
  $('#dialog-text').on('keydown', function(event) {
    if (event.keyCode == 13) {
      ws.send(JSON.stringify({command: "dialog", data: {text: $('#dialog-text').val()}}));
      if (document.getElementById('enter_key_flag').checked) {
        $('#dialog-text').val('');
      }
    }
  });
  $('#send-text').on('click', function() {
    if ($('#voice').val() == '') {
      alert("ボイスファイルを指定してください。");
    } else {
      ws.send(JSON.stringify({command: "say", data: {text: $('#speech-text').val(), voice: $('#voice').val()}}));
    }
  });
  $('#send-text').on('click', function() {
    ws.send(JSON.stringify({command: "dialog", data: {text: $('#dialog-text').val()}}));
  });

  $('#speech-text').on('change keyup', function() {
    buttonEnable($('#send-text'));
  });

  function parseMessage(messageData) {
    // WebSocketで受け取ったJSONメッセージの処理
    response = messageData['response']
    if (response == 'voice_list') {
      $("#voice").children().remove();
      for (var i = 0, len = messageData['data'].length; i < len; i++) {
        $("#voice").append($("<option>").val(messageData['data'][i]).text(messageData['data'][i]));
      }
    }
  }

  function buttonEnable(button) {
    button.prop("disabled", false);
    button.prop("className", "button");
  }

  function buttonDisable(button) {
    button.prop("disabled", true);
    button.prop("className", "button-disable");
  }

  function printJSON() {
    $('#json-data').val(JSON.stringify(json, null, '  '));
  }

  function updateJSON(data) {
      json = data;
      printJSON();
  }

  function showPath(path) {
    $('#path').text(path);
  }

})();
