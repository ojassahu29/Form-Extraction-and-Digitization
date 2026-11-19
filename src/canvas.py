"""Small Streamlit v2 component for interactive rectangular field selection."""

import base64
import io

import streamlit as st


_JS = r"""
const instances = new WeakMap();
export default function(component) {
  const {data, parentElement, setStateValue} = component;
  let box = instances.get(parentElement);
  if (box && box.key !== data.key) {
    box.root.remove();
    instances.delete(parentElement);
    box = null;
  }
  if (!box) {
    const root = document.createElement('div');
    root.className = 'field-selector';
    root.style.width = data.width + 'px';
    root.style.aspectRatio = data.width + '/' + data.height;
    root.style.backgroundImage = `url(${data.image})`;
    const layer = document.createElement('div');
    layer.className = 'field-layer';
    root.appendChild(layer);
    parentElement.appendChild(root);
    box = {root, layer, key:data.key, boxes: structuredClone(data.initial), active:null};
    instances.set(parentElement, box);
    const position = (event) => {
      const rect = root.getBoundingClientRect();
      return {
        x: Math.max(0, Math.min(data.width, (event.clientX-rect.left)*data.width/rect.width)),
        y: Math.max(0, Math.min(data.height, (event.clientY-rect.top)*data.height/rect.height))
      };
    };
    const publish = () => setStateValue('boxes', structuredClone(box.boxes));
    const draw = () => {
      layer.replaceChildren();
      box.boxes.forEach((region, index) => {
        const element = document.createElement('div');
        element.className = 'field-box';
        element.style.left = region.left/data.width*100 + '%';
        element.style.top = region.top/data.height*100 + '%';
        element.style.width = region.width/data.width*100 + '%';
        element.style.height = region.height/data.height*100 + '%';
        const label = document.createElement('span');
        label.textContent = String(index+1);
        element.appendChild(label);
        const handle = document.createElement('i');
        handle.className = 'field-handle';
        element.appendChild(handle);
        const del = document.createElement('button');
        del.type = 'button'; del.className='field-delete'; del.textContent='×'; del.title='Delete region';
        del.addEventListener('pointerdown', event => event.stopPropagation());
        del.onclick = (event) => {event.stopPropagation(); box.boxes.splice(index,1); draw(); publish();};
        element.appendChild(del);
        element.addEventListener('pointerdown', event => {
          event.preventDefault(); event.stopPropagation();
          const p = position(event);
          box.active = {kind:event.target===handle?'resize':'move', index, start:p, original:{...region}};
          root.setPointerCapture(event.pointerId);
        });
        layer.appendChild(element);
      });
    };
    root.addEventListener('pointerdown', event => {
      if (event.target !== root && event.target !== layer) return;
      event.preventDefault();
      const p = position(event);
      const index = box.boxes.push({id:crypto.randomUUID(), left:p.x, top:p.y, width:1, height:1})-1;
      box.active = {kind:'draw', index, start:p};
      root.setPointerCapture(event.pointerId);
      draw();
    });
    root.addEventListener('pointermove', event => {
      if (!box.active) return;
      const p = position(event), a = box.active, r = box.boxes[a.index];
      if (a.kind === 'draw') {
        r.left = Math.min(a.start.x,p.x); r.top = Math.min(a.start.y,p.y);
        r.width = Math.abs(p.x-a.start.x); r.height = Math.abs(p.y-a.start.y);
      } else if (a.kind === 'move') {
        r.left = Math.max(0,Math.min(data.width-r.width,a.original.left+p.x-a.start.x));
        r.top = Math.max(0,Math.min(data.height-r.height,a.original.top+p.y-a.start.y));
      } else {
        r.width = Math.max(1,Math.min(data.width-r.left,a.original.width+p.x-a.start.x));
        r.height = Math.max(1,Math.min(data.height-r.top,a.original.height+p.y-a.start.y));
      }
      draw();
    });
    root.addEventListener('pointerup', event => {
      if (!box.active) return;
      const r = box.boxes[box.active.index];
      if (r.width < 4 || r.height < 4) box.boxes.splice(box.active.index,1);
      box.active = null; draw(); publish();
    });
    draw();
  }
  return () => {};
}
"""

_CSS = """
.field-selector {position:relative;background-size:100% 100%;background-repeat:no-repeat;touch-action:none;max-width:100%;border:1px solid #888;box-sizing:border-box;}
.field-layer {position:absolute;inset:0;pointer-events:none;}
.field-box {position:absolute;border:2px solid #d62828;background:rgba(214,40,40,.12);box-sizing:border-box;cursor:move;pointer-events:auto;}
.field-box span {position:absolute;top:-2px;left:-2px;background:#d62828;color:white;padding:1px 5px;font:bold 13px sans-serif;}
.field-handle {position:absolute;right:-5px;bottom:-5px;width:11px;height:11px;background:#d62828;cursor:nwse-resize;}
.field-delete {position:absolute;right:-2px;top:-2px;background:#fff;color:#a00;border:1px solid #a00;cursor:pointer;font:bold 16px sans-serif;line-height:16px;padding:0 3px;}
"""

_component = st.components.v2.component("field_rectangle_selector", js=_JS, css=_CSS)


def select_regions(image, initial, key):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    uri = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
    result = _component(data={"image": uri, "width": image.width, "height": image.height, "initial": initial, "key": key}, key=key, on_boxes_change=lambda: None)
    boxes = result.get("boxes")
    return boxes if boxes is not None else initial
