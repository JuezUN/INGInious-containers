��          �               �     �  q   �  G   N     �  E   �  ^   �  6   T  P  �  �   �  �  �  �  0     �     �  $   �     	  K   	     i	  1   �	  /   �	     �	  c   �	     X
  "   r
  O   �
  #   �
  :   	  �  D     �  �   �  ^   x     �  V   �  _   K  G   �  ]  �  �   Q  �    �  �     I     a  .   ~     �  T   �  *     :   D  9        �  {   �     S  ,   k  h   �  2     S   4   	- Case {}: {} 
                                        <br><strong>Output difference:</strong><pre>{case_output_diff}</pre><br> 
@@ Diff is too big and was clipped. The error might be in last lines.
 **Compilation error**:

 <br><strong>Custom feedback:</strong><br><pre>{custom_feedback}</pre> <br><strong>{}:</strong> There was an error while running your notebook: <br><pre>{}</pre><br> <p>Custom feedback</p><pre>{custom_feedback}</pre><br> <p>Input preview: {title_input}</p>
                                  <pre class="input-area" id="{block_id}-input">{input_text}</pre>
                                  <div id="{title_input}_download_link"></div>
                                  <script>createDownloadLink("{title_input}");</script>
                                   <strong>Executed code:</strong><pre class="language-python"><code class="language-python" data-language="python">{case_code}</code></pre><script>highlight_code();</script> <ul class="list_disc" style="font-size:12px; list-style-type: square;"><li>
            <strong>Case {case_id}:</strong><a class="btn btn-default btn-link btn-xs" role="button" data-toggle="collapse" 
            href="#{case_panel_id}" aria-expanded="false"aria-controls="{case_panel_id}">Show debug info (only for staff)</a>
            <div class="collapse" id="{case_panel_id}">{debug_info}</div></li></ul>
             <ul class="list_disc" style="font-size:12px; list-style-type: square;"><li>
        <strong>Case {case_id}:</strong><a class="btn btn-default btn-link btn-xs" role="button" data-toggle="collapse" 
        href="#{case_panel_id}" aria-expanded="false"aria-controls="{case_panel_id}">Show debug info</a>
        <div class="collapse" id="{case_panel_id}">{debug_info}</div></li></ul>
         Compilation failed. Expand test results Expand test results (only for staff) Factory does not exist:  Failed downloading dataset, make sure the container has access to Internet. Long output, it was reduced. The memory limit was exceeded during compilation. The time limit was exceeded during compilation. Toggle diff Unexpected error while parsing the notebook. Check that your notebook runs correctly and try again. Unhandled grader result:  Your code did not run successfully Your code did not run successfully: <strong>%s</strong>, check the error below. Your code exceeded the output limit Your code finished successfully. Check your output below
. Project-Id-Version:  1.0
Report-Msgid-Bugs-To: uncode_fibog@unal.edu.co
POT-Creation-Date: 2022-12-20 17:05-0500
PO-Revision-Date: 2021-05-13 18:59-0500
Last-Translator: Cristian González <crdgonzalezca@unal.edu.co>
Language: es
Language-Team: es <LL@li.org>
Plural-Forms: nplurals=2; plural=(n != 1)
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.9.1
 	- Caso {}: {} 
                                        <br><strong>Diferencia en la salida estándar:</strong><pre>{case_output_diff}</pre><br> 
@@ La diferencia es muy grande y fue recortada. El error puede estar en la últimas líneas.
 **Error de compilación**:

 <br><strong>Retroalimentación personalizada:</strong><br><pre>{custom_feedback}</pre> <br><strong>{}:</strong> Hubo un error mientras se ejecutaba el notebook: <br><pre>{}</pre><br> <p>Retroalimentación personalizada</p><pre>{custom_feedback}</pre><br> <p>Vista previa de la entrada: {title_input}</p>
                                  <pre class="input-area" id="{block_id}-input">{input_text}</pre>
                                  <div id="{title_input}_download_link"></div>
                                  <script>createDownloadLink("{title_input}");</script>
                                   <strong>Código ejecutado:</strong><pre class="language-python"><code class="language-python" data-language="python">{case_code}</code></pre><script>highlight_code();</script> <ul class="list_disc" style="font-size:12px; list-style-type: square;"><li>
        <strong>Caso {case_id}:</strong><a class="btn btn-default btn-link btn-xs" role="button" data-toggle="collapse" 
        href="#{case_panel_id}" aria-expanded="false"aria-controls="{case_panel_id}">Mostrar información de depuración (solo para staff)</a>
        <div class="collapse" id="{case_panel_id}">{debug_info}</div></li></ul>
         <ul class="list_disc" style="font-size:12px; list-style-type: square;"><li>
        <strong>Caso {case_id}:</strong><a class="btn btn-default btn-link btn-xs" role="button" data-toggle="collapse" 
        href="#{case_panel_id}" aria-expanded="false"aria-controls="{case_panel_id}">Mostrar información de depuración</a>
        <div class="collapse" id="{case_panel_id}">{debug_info}</div></li></ul>
         La compilación falló. Expandir resultados del test Expandir resultados del test (solo para staff) El Factory no existe:  Falló descargando el dataset, asegúrese que el contenedor tiene acceso a Internet. Salida estándar muy grande, fue reducida. La memoria límite fue excedida en tiempo de compilación. El tiempo límite fue excedido en tiempo de compilación. Alternar panel de diferencias Error inesperado mientras se analizaba el notebook. Revise que el notebook se ejecute correctamente y vuélvalo a intentar. Resultado no manejado:  El código no se ejecutó satisfactoriamente El código no se ejecutó satisfactoriamente: <strong>%s</strong>, revise el error en la parte de abajo. El código excedió el límite de salida estándar El código finalizó satisfactoriamente. Revise el resultado en la parte de abajo
. 