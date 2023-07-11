from src.error import ERROR
from src.Container import (
    build as containerBuilder,
    delete as containerDelete,
    search as containerSearch,
    status as containerStatus,
)

from fastapi import FastAPI
from jsonset import buildInfo, statusSetting


api = FastAPI()


@api.post("/container/build", tags=["Container"])
async def containerBuild(buildInfo: buildInfo):
    """
    해당 API는 개발 환경 컨테이너를 배포 하기 위한 프로그램입니다.

    해당 API를 사용하기 위해서 필요한 파라미터는 아래와 같습니다.

    |    변수명    | 타입 | 기본값  |                     설명                      |
    | :----------: | :--: | :-----: | :-------------------------------------------: |
    | projectName  | str  |    -    |                 프로젝트 이름                 |
    |  Processor   | str  |   CPU   |            프로세서 할당 파라미터             |
    |      OS      | str  | Ubuntu  |   개발환경 컨테이너 운영체제 할당 파라미터    |
    |     Type     | str  | Jupyter |   개발환경 컨테이너 접속 방식 할당 파라미터   |
    |   password   | str  |  None   | 프로젝트 배포 컨테이너 비밀번호 할당 파라미터 |
    | databaseList | list |  None   |   데이터베이스 컨테이너 배포 할당 파라미터    |

    결과값으로는 아래와 같이 출력된다.

    또한 해당 API에서는 지원하는 타입이 지정되어있다.

    지정된 타입은 아래와 같이 구성되어있다.

    | 변수명       | 타입 | 지원 타입 (대소문자 확인)    |
    | :------------: | :----: | :----------------------------: |
    | Processor    | str  | CPU, GPU                     |
    | OS           | str  | ubuntu, centos, rockylinux, tensorflow   |
    | Type         | str  | SSH, Jupyter                 |
    | databaseList | list | mysql, mariadb, mongo, redis |

    대소문자 확인후 대입을 해야 에러 발생이 되지 않는다.

    또한 이러한 문자 해석은 따로 필터를 거치지 않고 구현되어있다.


    ## Status Code 200

    해당 에러는 정상적으로 배포가 되었습니다.

    ```
    {
        "devContainer": {
            "status": int,
            "port": int
        },
        "databaseContainer": [
            {
            "database": str,
            "status": bool
            }
        ]
    }
    ```


    ## Status Code 400

    해당 에러는 Docker Image가 Pull이 되지 않은경우 발생이 될수있는이슈입니다.
    Installer를 다시 실행후 처리 하세요.

    ```
    {
        "msg": "You do not have permission.",
        "NotBuildContainer": "The name is already registered."
    }
    ```


    ## Status Code 503

    해당 에러는 프로젝트 이름이 중복되었을때 발생되는 에러이다.
    프로젝트 이름을 다른걸로 변경하여 재시도 하시오.

    ```
    {
        "msg": "You do not have permission.",
        "NotBuildContainer": "The name is already registered."
    }
    ```

    """

    devContainerBuilder = None
    databaseContainers = None

    """프로젝트 이름 중복확인"""
    if containerSearch.containerNameCheck(buildInfo.projectName) == False:
        ContainerBuilderClass = containerBuilder.Build(
            buildInfo.projectName,
            buildInfo.OS,
            buildInfo.password,
            buildInfo.databaseList,
        )  # 컨테이너 빌드 파라미터 기본값

        # 컨테이너 접속 타입 빌드
        if buildInfo.Type == "Jupyter" or buildInfo.Type == "jupyter":
            devContainerBuilder = ContainerBuilderClass.jupyter()

        elif buildInfo.Type == "SSH" or buildInfo.Type == "ssh":
            devContainerBuilder = ContainerBuilderClass.ssh()

        if devContainerBuilder["status"] == 200:
            """데이터 베이스 컨테이너 빌드"""
            if buildInfo.databaseList != None:
                databaseContainers = ContainerBuilderClass.database()

            return {
                "devContainer": {
                    "status": devContainerBuilder["status"],
                    "port": devContainerBuilder["port"],
                },
                "databaseContainer": databaseContainers,
            }

        elif devContainerBuilder["status"] == 400:
            return ERROR.API_Error_Messages(
                devContainerBuilder["status"],
                "NoContainerImage",
                "No container image required",
            )  # 개발환경 컨테이너 빌드 에러인경우

    else:
        return ERROR.API_Error_Messages(
            503, "NotBuildContainer", "The name is already registered."
        )  # 프로젝트 이름이 곂칠때 에러


@api.put("/project/container/status", tags=["Container"])
async def projectContainerStatus(projectName: str, statusSetting: statusSetting):
    """
    해당 함수는 프로젝트 컨테이너 실행 관리를 위한 프로그램입니다.
    
    해당 API를 사용하기 위해서 필요한 파라미터는 아래와 같습니다.

    |   변수명    | 타입 | 기본값 |     설명      |
    | :---------: | :--: | :----: | :-----------: |
    | projectName | str  |   -    | 프로젝트 이름 |
    | statusSetting | str  |   -    | 프로젝트 컨테이너 상태 정보 |

    결과값으로는 아래와 같이 출력됩니다.

    ## Status Code 200
    {
        "Status": {
            "devContainer": bool,
            "databaseContainer": {
                str: bool,
                ...
            }
        },
    }

    ## Status Code 404

    ```json
    {
        "msg": "Not found",
        "NotFoundProjects": "Projects that cannot be found"
    }
    ```
    """
    if containerSearch.containerNameCheck(projectName) == True:
        return containerStatus.status(projectName, statusSetting).project()

    else:
        return ERROR.API_Error_Messages(
            404, "NotFoundProjects", "Projects that cannot be found"
        )  # 프로젝트 컨테이너가 없는경우


@api.delete("/container/remove", tags=["Container"])
async def containerRemove(projectName: str):
    """
    해당 API는 개발 환경 컨테이너를 삭제 하기 위한 프로그램입니다.

    해당 API를 사용하기 위해서 필요한 파라미터는 아래와 같습니다.

    |   변수명    | 타입 | 기본값 |     설명      |
    | :---------: | :--: | :----: | :-----------: |
    | projectName | str  |   -    | 프로젝트 이름 |

    결과값으로는 아래와 같이 출력됩니다.

    ## 프로젝트 삭제 결과
    ```
    {
        "projectName": str,
        "projectStatus": {
            "devContainer": bool,
            "databaseContainers": dict[bool],
            "containersNetwork": bool,
            "containersVolume": bool
        },
    }
    ```

    # 프로젝트 삭제가 이미 되었거나 없는경우

    ```
    {
        "msg": "Not found",
        "NotFoundProjects": "Projects that cannot be found"
    }
    ```

    """
    if containerSearch.containerNameCheck(projectName) == True:
        return containerDelete.remove(projectName).Project()  # 프로젝트 컨테이너 삭제

    else:
        return ERROR.API_Error_Messages(
            404, "NotFoundProjects", "Projects that cannot be found"
        )  # 프로젝트 컨테이너가 없는경우


@api.get("/container/find", tags=["Container"])
async def containerFind(projectName: str = None):
    """
    해당 API는 개발 환경 컨테이너를 삭제 하기 위한 프로그램입니다.

    해당 API를 사용하기 위해서 필요한 파라미터는 아래와 같습니다.

    |   변수명    | 타입 | 기본값 |     설명      |
    | :---------: | :--: | :----: | :-----------: |
    | projectName | str  |  None  | 프로젝트 이름 |


    또한 해당 기능은 `projectName` 값을 넣으면 **단일 프로젝트 정보**를 출력되며 넣지 않는경우 **복수 프로젝트 정보**를 출력하게된다.

    결과값으로는 아래와 같이 출력된다.


    ## 단일 프로젝트 정보

    ```
    {
        "projectName": str,
        "createdTimes": float,
        "devContainer": {
            "type": str,
            "gpu": bool,
            "status": bool,
            "port": int,
        },
        "databaseContainers": {
            str: {
                "status": bool,
                "ip": str,
            }
        }
    }
    ```


    ## 복수 프로젝트 정보

    ```
    [
        {
            "projectName": str,
            "devContainer": {
                "Type": str,
                "status": bool,
                "port": int,
                "gpu": int,
                "createdTimes": float,
            },
            "databaseContainer": [
                str
            ],
        },
        ...
    ]
    ```


    ## 복수 프로젝트 정보에서 데이터가 없는경우

    ```
    []
    ```


    ## Status Code 404

    ```
    {
        "msg": "Not found",
        "NotFoundProjects": "Projects that cannot be found"
    }
    ```
    """
    return containerSearch.Search(projectName).info()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(api, host="0.0.0.0", port=80)