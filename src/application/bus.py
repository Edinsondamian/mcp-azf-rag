import logging
from typing import Any, Dict, Type, TypeVar, Generic

logger = logging.getLogger(__name__)

TCommand = TypeVar("TCommand")
TQuery = TypeVar("TQuery")
TResult = TypeVar("TResult")


class Command:
    """Clase base para todos los Commands (Modificaciones de estado)."""
    pass


class Query:
    """Clase base para todas las Queries (Lecturas/Consultas de estado)."""
    pass


class CommandHandler(Generic[TCommand, TResult]):
    """Interfaz base para manejadores de comandos."""
    def handle(self, command: TCommand) -> TResult:
        raise NotImplementedError


class QueryHandler(Generic[TQuery, TResult]):
    """Interfaz base para manejadores de consultas."""
    def handle(self, query: TQuery) -> TResult:
        raise NotImplementedError


class CQRSMediator:
    """
    Mediador para desacoplar el emisor del receptor en la arquitectura CQRS.
    Maneja el registro y despacho de Commands y Queries.
    """
    def __init__(self) -> None:
        self._command_handlers: Dict[Type[Command], CommandHandler[Any, Any]] = {}
        self._query_handlers: Dict[Type[Query], QueryHandler[Any, Any]] = {}

    def register_command_handler(
        self,
        command_cls: Type[TCommand],
        handler: CommandHandler[TCommand, Any]
    ) -> None:
        self._command_handlers[command_cls] = handler
        logger.debug("Registrado CommandHandler para %s", command_cls.__name__)

    def register_query_handler(
        self,
        query_cls: Type[TQuery],
        handler: QueryHandler[TQuery, Any]
    ) -> None:
        self._query_handlers[query_cls] = handler
        logger.debug("Registrado QueryHandler para %s", query_cls.__name__)

    def send(self, command: Command) -> Any:
        """Despacha un Command a su CommandHandler correspondiente."""
        cmd_type = type(command)
        handler = self._command_handlers.get(cmd_type)
        if not handler:
            raise KeyError(f"No hay CommandHandler registrado para {cmd_type.__name__}")
        return handler.handle(command)

    def query(self, query: Query) -> Any:
        """Despacha una Query a su QueryHandler correspondiente."""
        qry_type = type(query)
        handler = self._query_handlers.get(qry_type)
        if not handler:
            raise KeyError(f"No hay QueryHandler registrado para {qry_type.__name__}")
        return handler.handle(query)


# Instancia singleton por defecto
mediator = CQRSMediator()
