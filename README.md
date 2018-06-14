# Discord_TRPG_DiceBot

## Bot作成および導入
[Discordディベロッパーページ](https://discordapp.com/developers/applications/me)にアクセス．  
「マイアプリ」→「新しいアプリ」で登録．  
「Bot」→「Botユーザーを作成」→「実行します」でBotを作成．  
「トークン：クリックして表示」を押して出てくるBot用トークンを記録しておく．  
「main.py」と同じ階層に「token.txt」を作成し，そのファイルに先ほどのBot用トークンを記述．  

「Generate OAuth2 URL」→「COPY」でコピーしたURLを導入したいサーバーの管理者にアクセスしてもらい，BOTをサーバーに参加させる．  

「main.py」を起動．  
	●必要ライブラリ  
	・diccord.py  
	`python -m pip install -U discord.py`  
	・PLY(字句解析/構文解析ライブラリ)  
	`pip install ply`  
	・numpy(学術計算ライブラリ)  
	`pip install numpy`  	
<!--
	・PyNacl，libffi-dev，ffmpeg(音楽を鳴らすためのライブラリ)  
	`pip install pynacl`  
	Mac：`brew install libffi`，Ubuntu：`sudo apt install libffi-dev`  
	Mac：`brew install ffmpeg`，Ubuntu：`sudo apt install ffmpeg`  
-->
## コマンド一覧（詳しくは「!dhelp」で）
!d コマンド         ：このコマンドから始まる発言をこのDiceBot用記法と認識する．  
                   ：改行を入れることで行ごとに別の処理ができる．  
                   ：ダイスを振る処理を行った時に，発言者がvoiceチャンネルに接続していればダイス音が再生される．  
!dsc コマンド       ：このコマンドではシークレットダイスを振る処理を行う．  
                   ：結果は個人チャットに返信される．  
!dhelp             ：ヘルプコマンドを表示する．  
!dhelp システム名    ：システムのコマンド説明を表示する．  
                   ：対応システム：COC-クトゥルフの呼び声，SW-ソード・ワールド2.0  
                               LHZ-ログ・ホライズンTRPG，MK-迷宮キングダム  
!dget              ：発言者の登録した数値・コマンド・ターンカウントを表示する．  
!dgetall           ：そのサーバーで登録された数値・コマンド・ターンカウントを表示する．  
!ddel              ：発言者の登録した数値・コマンド・ターンカウントを削除する．  
!ddel [登録名]      ：登録名と一致する数値を削除する．  
!ddel {登録名}      ：登録名と一致するコマンドを削除する．  
!ddel T[登録名]     ：登録名と一致するターンカウントを削除する．  
!dallcommand       ：「!d」から始まらなくなくてもコマンドとして認識するように設定する．  
                   ：もう一度呼び出すと通常に戻す．  
!dlogout		   ：接続されている（数値やコマンド等を記憶している）サーバーが1個だけならプログラムを終了する

<!--
## 使用楽曲
[ダイス音・2（2D10），ニコニ・コモンズ](http://commons.nicovideo.jp/material/nc42340)  
-->
