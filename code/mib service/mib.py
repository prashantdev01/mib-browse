from pysnmp.hlapi.asyncio import ObjectIdentity
from fastapi import FastAPI, HTTPException, APIRouter, File, UploadFile, HTTPException
from pysnmp.smi import builder, view,compiler
import os
import subprocess
from fastapi.responses import JSONResponse

router = APIRouter()

print("pysnmp.hlapi installed successfully!")

def get_all_mib_modules():
    mib_modules = []
    mibs_directory = "venv\Lib\site-packages\pysnmp\smi\mibs"

    for file_name in os.listdir(mibs_directory):
        if file_name.endswith(".py") and file_name != "__init__.py":
            module_name = file_name[:-3]
            mib_modules.append(module_name)

    return mib_modules
# Api to Get and return all MIB modules
@router.get("/mib_modules/", response_model=list[str],description="dev-Pralshant",tags=['MIB'])
def read_mib_modules():
    all_mib_modules = get_all_mib_modules()
    data = {'status' : 'sucess', 'error_code' : 0, 'data' : all_mib_modules }
    return JSONResponse(data)



def load_mib_module(module_name):
    mib_builder = builder.MibBuilder()
    print("mib_builder", mib_builder)
    try:
        mib_builder.loadModules(module_name)
    except Exception as e:
        print(f"Error loading MIB module {module_name}: {e}")
    mib_view_controller = view.MibViewController(mib_builder)
    return mib_view_controller

def get_all_oids_in_module(module_name):
    mib_view_controller = load_mib_module(module_name)
    mib_tree_root = mib_view_controller.mibBuilder.mibSymbols[module_name]

    def traverse_mib_tree(node, parent_oid):
        result = []
        for sub_id, sub_node in node.items():
            current_oid = parent_oid + (sub_id,)
            result.append(current_oid)
            if isinstance(sub_node, dict):
                result.extend(traverse_mib_tree(sub_node, current_oid))
        return result

    return traverse_mib_tree(mib_tree_root, ())

def get_data_type(module_name, numeric_oid):
    try:
        mibBuilder = builder.MibBuilder()
        compiler.addMibCompiler(mibBuilder, sources=['venv\Lib\site-packages\pysnmp_mibs'])
        mibBuilder.loadModules(module_name)
        mibView = view.MibViewController(mibBuilder)
        oid_tuple = tuple(map(int, numeric_oid.split('.')))
        modName, symName, suffix = mibView.getNodeLocation(oid_tuple)
        mibNode, = mibBuilder.importSymbols(modName, symName)
        if hasattr(mibNode, 'syntax'):
            data_type = mibNode.syntax.__class__.__name__
        else:
            data_type = "Unknown" 
        return data_type
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# Api to get all oids names from module
@router.get("/get/{module_name}",description="dev-Prashant",tags=['MIB'])
async def get_oids_in_module(module_name: str):
    try:
        oids = get_all_oids_in_module(module_name)
        response = {"module_name": module_name, "oids": oids}
        # return response
        data = {'status' : 'sucess', 'error_code' : 0, 'data' : response }
        return JSONResponse(data)
    except NameError as ne:
        data = {'status' : 'error', 'error_code' : 103, 'message' : 'Error : {0}'.format(ne)}
        return JSONResponse(data)
    
    except KeyError as ke:
        data = {'status' : 'error', 'error_code' : 102, 'message' : 'Error : {0} is required'.format(ke)}
        return JSONResponse(data)
    
    except Exception as e:
        data = {'status' : 'error', 'error_code' : 101, 'message' : 'Error : {0}'.format(e)}        
        return JSONResponse(data)   
# Api to get all oids with their data type from module
@router.get("/get_numeric_oid/{module_name}/{oid_name}",description="dev-Prashant",tags=['MIB'])
async def get_numeric_oid(module_name: str, oid_name: str):
    try:
        mib_builder = builder.MibBuilder()
        mib_builder.loadModules(module_name)
        mib_view_controller = view.MibViewController(mib_builder)
        oid = ObjectIdentity(module_name, oid_name).resolveWithMib(mib_view_controller)
        numeric_oid = '.'.join(map(str, oid.getOid()))
        data_type = get_data_type(module_name,numeric_oid)


        response = {"data_type": data_type,"numeric_oid": numeric_oid}
        data = {'status' : 'sucess', 'error_code' : 0, 'data' : response }
        return JSONResponse(data)
    except NameError as ne:
        data = {'status' : 'error', 'error_code' : 103, 'message' : 'Error : {0}'.format(ne)}
        return JSONResponse(data)
    
    except KeyError as ke:
        data = {'status' : 'error', 'error_code' : 102, 'message' : 'Error : {0} is required'.format(ke)}
        return JSONResponse(data)
    
    except Exception as e:
        data = {'status' : 'error', 'error_code' : 101, 'message' : 'Error : {0}'.format(e)}        
        return JSONResponse(data)

@router.post("/upload-mib/",description="dev-Prashant",tags=['MIB'])
async def upload_mib(file: UploadFile = File(...)):
    try:
        if file.file is None:
            return JSONResponse({'status' : 'error', 'error_code' : 109, 'message' : "Uploaded file is empty"})
        valid_mib_mimetypes = ["application/octet-stream", "application/mib"] 
        if file.content_type not in valid_mib_mimetypes:
            return JSONResponse({'status' : 'error', 'error_code' : 109, 'message' : 'Uploaded file is not a valid .mib file'})
        upload_folder = "/project myself/mib"
        file_path = os.path.join(upload_folder, file.filename)

        with open(file_path, "wb") as mib_file:
            mib_file.write(file.file.read())
        command = [
            "mibdump.py",
            "--mib-source=project myself/mib",
            "--destination-format=pysnmp",
            "--destination-directory=/usr/local/lib/python3.9/site-packages/pysnmp_mibs",
            f"mib/{file.filename}"
        ]
        print(command)
        result = subprocess.run(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result)
        if result.returncode == 0:
            return JSONResponse({'status' : 'success','error_code' : 0, 'message':"MIB file uploaded and converted successfully"})
        else:
            missing_files = [mib.strip() for mib in result.stderr.decode().splitlines() if "Missing source MIBs" in mib]
            return JSONResponse({'status': 'error', 'error_code': 109, 'message': f"Missing files: {', '.join(missing_files)}"})
    except NameError as ne:
        data = {'status' : 'error', 'error_code' : 103, 'message' : 'Error : {0}'.format(ne)}
        return JSONResponse(data)
    
    except KeyError as ke:
        data = {'status' : 'error', 'error_code' : 102, 'message' : 'Error : {0} is required'.format(ke)}
        return JSONResponse(data)
    
    except Exception as e:
        data = {'status' : 'error', 'error_code' : 101, 'message' : 'Error : {0}'.format(e)}        
        return JSONResponse(data)




