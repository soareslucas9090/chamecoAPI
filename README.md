

# ChamecoAPI

<img align="center" alt="Python" width="30" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg"><span>&nbsp;&nbsp;&nbsp;</span>
<img align="center" alt="Django" width="30" src="https://cdn.worldvectorlogo.com/logos/django.svg"><span>&nbsp;&nbsp;&nbsp;</span>
<img align="center" alt="Django Rest Framework" height="40" src="https://i.imgur.com/dcVFAeV.png"><span>&nbsp;&nbsp;&nbsp;</span>
<img align="center" alt="PostgreSQL" width="36" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/postgresql/postgresql-original.svg"><span>&nbsp;&nbsp;&nbsp;</span>

## Segurança

O ChamecoAPI foi desenvolvido contendo total integração com o CortexAPI, onde o usuário, para fazer login, passa seu login e senha, mas estes não ficam guardados no bancode dados do Chameco, pois este por sua vez faz a requisição para o cortex enviando os dados para login e recebendo sua resposta. Com isso é gerado um token, este sim persistido, que identifica o acesso ao Access Token e Refresh Token obtidos no login do Cortex que ficam em cache por um certo período na aplicação.

Foram implementados filtros de pesquisa (query-params) na maioria das rotas para aplicação de filtros de pesquisas.

A documentação está na rota `chameco/api/schema/swagger/`

# Rodando o projeto

Primeiro é necessária a criação de um Ambiente Virtual do Python (necessário versão 3.8 ou posterior do Python, mas recomendamos a 3.11), ou `venv`, para isso basta executar `python -m venv venv`. Ao término é necessário ativar a venv, então na mesma pasta que foi criado a pasta do ambiente virtual, rode o comando `venv\scripts\activate` para Windows, ou `venv/bin/activate` praa Linux, e pronto.

Para instalar as dependências é necesário rodar o comando `pip install -r requirements.txt` com o Ambiente Virtual Ativo.
O código busca um arquivo `.env` para procurar as variáveis de ambiente necessárias, e caso não ache, usará as variáveis de ambiente instaladas no SO. O arquivo deve seguir os seguintes moldes:
```
secretKeyDjango=A chave secreta do Django, usada na criptografia de CSRF Token
debugMode=False
bdEngine=django.db.backends.postgresql
bdName=Nome do banco
bdUser=Usuário do Banco
bdPass=Senha do Banco
bdHost=Host do banco
bdPort=Porta do banco
allowedHosts=*
csrfTrustedOriginsANDcorsOriginWhitelist=IP do servidor que hosperdará o frontend da aplicação e permitirá acesso à API, caso seja mais de um, divida eles com virgulas sem espaço, como na variável abaixo
internalIPs=127.0.0.1,localhost,http://127.0.0.1,https://127.0.0.1,http://localhost,https://localhost
urlBase=A url base do Cortex que será usada na integração com o sistema. Exemplo: https://cortexifpi.ifpi.edu.br/
```
Colocar o arquivo `.env` na raiz do projeto ou adicionar estas variáveis diretamente no sistema.

Faça a criação do banco de dados com o comando `python manage.py migrate`.

### O comando `python manage.py migrate` é muito importante de ser feito toda vez que se atualiza o sistema, ele é quem cria vários registros do sistema do Cortex.

Execute um `python manage.py collectstatic` para criar os arquivos estáticos da documentação da API, pois sem este comando, o Swagger não consegue executar os arquivos CSS e JS necessários para rodar a sua interface. 

Com tudo configurado, o servidor para rodar o sistema em qualquer computador com Windows 8+ ou Server 2012+ é o "Waitress", e o comando para iniciar é (lembrando que a *venv* deve estar ativada, e o comando deve ser executado na raiz do projeto):
`waitress-serve --port=8000 chameco.wsgi:application`

O servidor para rodar o sistema em um computador Linux é o "Gunicorn", e o comando é:
`gunicorn chameco.wsgi --workers 2 --bind :8000 --access-logfile -`

### ATENÇÃO
***ESTES COMANDOS RODAM O SERVIDOR APENAS EM HTTP, PARA RODAR EM HTTPS É NECESSÁRIO REALIZAR OS COMANDO APRESENTADOS NA PRÓXIMA SEÇÃO.***

O serviço rodará no IP local, sendo acessível pela porta 8000 (é necessário a liberação da porta no Firewall do sistema e da rede. A porta também pode ser mudada por qualquer uma disponível). Exemplo: Servidor com IP `10.7.1.10`, o serviço ficará disponível em `http://10.7.1.10:8000`. Para rodar o sistema em HTTPS é necessário configurações adicionais no servidor.

## HTTPS

Como dito acima, os comandos do Waitress e Gunicorn rodam o servidor apenas em HTTP, para rodar no protocolo HTTPS, é preciso de um servidor de *proxy reverso*. Neste tutorial será usado o Nginx em um SO Windows.

### 1º - Gerando certificado SSL autoassinado

(Se você possuir um certificado emitido por um cliente de certificação, pode pular este passo)

- Instale o OpenSSL Light. [Link aqui](https://slproweb.com/products/Win32OpenSSL.html).
- Escolha a opção de copiar as DLLs do OpenSSL para o diretório `/bin` da aplicação.
- Adicione o Diretório de instalação ao Path do Windows (`C:\Program Files\OpenSSL-Win64\bin` por padrão).
- Abra o Powershell como administrador, e execute `New-SelfSignedCertificate -DnsName "localhost" -CertStoreLocation "cert:\LocalMachine\My" -NotAfter (Get-Date).AddYears(5)`. Isso irá criar um certificado autoassinado com o DNS `localhost` e o coloca no Windows Certificate Store.
- Exporte o certificado em formato `.pfx` com os seguintes códigos:
-- `$cert = Get-ChildItem -Path cert:\LocalMachine\My | Where-Object { $_.Subject -like "CN=localhost" }`
-- `$pwd = ConvertTo-SecureString -String "password" -Force -AsPlainText` (substitua `password` pela senha que desenha colocar no certificado.
-- `Export-PfxCertificate -Cert $cert -FilePath C:\caminho\do\certificado.pfx -Password $pwd`
- Separe o certificado `.pfx` em dois arquivos `.pem`:
-- O código do certificado com o código `openssl pkcs12 -in C:\path\to\cert.pfx -clcerts -nokeys -out C:\caminho\do\certificado.pem`
-- A chave privada do certicado com o código `openssl pkcs12 -in C:\path\to\cert.pfx -nocerts -out C:\caminhi\da\chave.pem -nodes`

### 2º - Instalando o Nginx

- Faça o download do Nginx para windows em >https://nginx.org/en/download.html.
- Extraia o `.zip` para a raiz do Disco Loca (C:).
- Vá até `C:\nginx\nginx.conf` e abra este arquivo no editor de texto de sua preferência
- Apague todo o conteúdo, e cole o código abaixo, personalizando o que for necessário:
```nginx.conf
worker_processes 1; # Número de processos de trabalho

events {
worker_connections 128; # Número máximo de conexões simultâneas
}

http {
	include mime.types;
	default_type application/octet-stream;

	server {
		listen 80; # A porta HTTP, que o Nginx estará escutando

		server_name localhost; # Substitua polo seu domínio ou deixe localhost
			
		# Redirecionar todas as requisições para HTTPS
		return 301 https://$host$request_uri;
	}	

	server {
		listen 443 ssl; # A porta HTTPS, que o Nginx estará escutando
		
		server_name localhost; # Substitua polo seu domínio ou deixe localhost

		ssl_certificate C:/caminho/do/certificado.pem; # Caminho para o certificado

		ssl_certificate_key C:/caminho/da/chave.pem; # Caminho para a chave privada

		location / {

			proxy_pass http://127.0.0.1:8000; # onde o Waitress estará ouvindo

			proxy_set_header Host $host;

			proxy_set_header X-Real-IP $remote_addr;

			proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

			proxy_set_header X-Forwarded-Proto $scheme;

		}

	}

}
```
- Desta forma, as requições feitas em http://127.0.0.1 ou http://localhost serão automaticamente redirecionadas para https://127.0.0.1 ou https://localhost.

### ATENÇÃO
***O SERVIDOR NGINX E O WAITRESS DEVEM RODAR EM PARALELO***

- Agora vá em `C:\nginx`, abra uma janela do CMD e execute o comando `nginx -t`. Deverá informar que está tudo OK com as configurações.
- Por fim, ainda em `C:\nginx`, execute `start nginx` no CMD. O processo do Nginx rodará de fundo.

## Inserção de Usuários e Dados em lote

Para a inserção em lote de Usuários é necessário rodar o script `inserir_usuarios.py` presente em `./insert_users/` enquanto o servidor está ativo, pois a inserção é feita com os endpoints da API. 
Antes da execução, abra o script e edite a variável `API_URL` para indicar o a url em que o sistema está sendo rodado, por exemplo: `"http://localhost:8000/chameco/api/v1/"` (é necessário que as planilhas alunos.xlsx, servidores.xslx e terceirizados.xslx estejam na mesma pasta do script.)
Para inserir os dados de salas, blocos e chaves é só rodar o script `inserir_dados.py` que está na raiz do projeto `./` enquanto o servidor está ativo, pois a inserção é feita com os endpoints da API. Para isso é necessário editar a variável `API_URL` da mesma forma como na inserção dos usuários, mas necessário também editar a variável `TOKEN` inserindo o token obtido ao fazer login (este token pode ser obtido consumindo a rota de login abrindo pelo próprio swagger da aplicação.)

